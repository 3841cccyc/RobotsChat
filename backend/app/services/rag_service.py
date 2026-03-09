from langchain_community.document_loaders import (
    TextLoader, 
    PyPDFLoader, 
    Docx2txtLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import settings
from typing import List, Optional, Dict
import os
import random


class RAGService:
    """RAG 服务 - 文档处理和向量检索"""
    
    def __init__(self):
        self.embeddings = None
        # 持久化目录
        self.persist_directory = "./vector_stores"
        os.makedirs(self.persist_directory, exist_ok=True)
    
    def _get_embeddings(self):
        """延迟初始化 embeddings"""
        if self.embeddings is None:
            api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                # 使用占位符key，初始化一个默认的embeddings
                api_key = "dummy-key-for-initialization"
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                dimensions=settings.embedding_dimensions,
                openai_api_key=api_key,
                openai_api_base=settings.openai_base_url or "https://api.openai.com/v1"
            )
        return self.embeddings
    
    def get_loader(self, file_path: str, file_type: str):
        """根据文件类型获取加载器"""
        if file_type == "pdf":
            return PyPDFLoader(file_path)
        elif file_type in ["doc", "docx"]:
            return Docx2txtLoader(file_path)
        else:
            return TextLoader(file_path, encoding="utf-8")
    
    def load_document(self, file_path: str, file_type: str) -> List:
        """加载文档"""
        try:
            loader = self.get_loader(file_path, file_type)
            documents = loader.load()
            return documents
        except Exception as e:
            print(f"Error loading document: {e}")
            return []
    
    def split_documents(self, documents: List, chunk_size: int = 1000, chunk_overlap: int = 200) -> List:
        """分割文档"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        return text_splitter.split_documents(documents)
    
    async def add_document(self, bot_id: int, file_path: str, file_type: str) -> str:
        """添加文档到向量库"""
        # 加载文档
        documents = self.load_document(file_path, file_type)
        if not documents:
            raise ValueError("无法加载文档")
        
        # 分割文档
        splits = self.split_documents(documents)
        
        # 创建向量库（每个机器人独立）
        collection_name = f"bot_{bot_id}"
        vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            collection_name=collection_name,
            persist_directory=self.persist_directory
        )
        
        # 持久化
        vector_store.persist()
        
        return vector_store._collection.name
    
    async def similarity_search(self, bot_id: int, query: str, k: int = 4) -> str:
        """相似性搜索"""
        collection_name = f"bot_{bot_id}"
        
        try:
            # 使用延迟初始化的 embeddings
            embeddings = self._get_embeddings()
            
            vector_store = Chroma(
                client=None,
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory
            )
            
            docs = vector_store.similarity_search(query, k=k)
            
            # 返回检索到的内容
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return ""
    
    async def delete_vector_store(self, bot_id: int) -> bool:
        """删除机器人的向量库"""
        collection_name = f"bot_{bot_id}"
        
        try:
            vector_store = Chroma(
                client=None,
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            vector_store.delete_collection()
            return True
        except Exception as e:
            print(f"Error deleting vector store: {e}")
            return False
    
    # ==================== 群聊向量存储 ====================
    
    def _get_group_collection_name(self, conversation_id: int) -> str:
        """获取群聊向量集合名称"""
        return f"group_chat_{conversation_id}"
    
    async def add_group_message(self, conversation_id: int, message: str, sender_name: str) -> bool:
        """
        添加群聊消息到向量库
        
        Args:
            conversation_id: 会话ID
            message: 消息内容
            sender_name: 发送者名称
        """
        try:
            collection_name = self._get_group_collection_name(conversation_id)
            embeddings = self._get_embeddings()
            
            vector_store = Chroma(
                client=None,
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory
            )
            
            # 添加消息到向量库
            # 使用消息内容作为 document，发送者作为 metadata
            metadata = {"sender": sender_name}
            vector_store.add_texts(texts=[message], metadatas=[metadata])
            vector_store.persist()
            
            return True
        except Exception as e:
            print(f"Error adding group message to vector store: {e}")
            return False
    
    async def search_group_history(
        self, 
        conversation_id: int, 
        query: str, 
        recent_messages: List[Dict] = None,
        k: int = 4
    ) -> str:
        """
        混合检索群聊历史：向量检索 + 最近消息缓存
        
        Args:
            conversation_id: 会话ID
            query: 查询内容
            recent_messages: 最近的消息缓存（用于补充时间上下文）
            k: 向量检索返回数量
            
        Returns:
            检索到的上下文字符串
        """
        try:
            collection_name = self._get_group_collection_name(conversation_id)
            embeddings = self._get_embeddings()
            
            vector_store = Chroma(
                client=None,
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory
            )
            
            # 向量检索
            docs = vector_store.similarity_search(query, k=k)
            vector_context = "\n".join([doc.page_content for doc in docs])
            
            # 最近消息缓存（保证连贯性）
            recent_context = ""
            if recent_messages:
                # 取最近10条消息
                recent = recent_messages[-10:]
                recent_context = "\n".join([
                    f"{msg.get('sender_name', '未知')}: {msg.get('content', '')}"
                    for msg in recent if msg.get('content')
                ])
            
            # 合并：最近消息优先，向量检索作为补充
            if recent_context and vector_context:
                return f"【最近对话】:\n{recent_context}\n\n【相关历史】:\n{vector_context}"
            elif recent_context:
                return f"【最近对话】:\n{recent_context}"
            elif vector_context:
                return f"【历史记录】:\n{vector_context}"
            else:
                return ""
                
        except Exception as e:
            print(f"Error searching group history: {e}")
            # 如果向量检索失败，至少返回最近的消息
            if recent_messages:
                recent = recent_messages[-10:]
                return "\n".join([
                    f"{msg.get('sender_name', '未知')}: {msg.get('content', '')}"
                    for msg in recent if msg.get('content')
                ])
            return ""
    
    @staticmethod
    def calculate_typing_delay(content: str) -> float:
        """
        模拟人类打字时间的延迟算法
        
        公式：delay = min(len(content) * 0.1, 5) + random.uniform(0.5, 1.5)
        
        Args:
            content: 生成的内容
            
        Returns:
            延迟时间（秒）
        """
        base_delay = min(len(content) * 0.1, 5)  # 最长5秒
        random_delay = random.uniform(0.5, 1.5)   # 随机0.5-1.5秒
        return base_delay + random_delay
    
    async def delete_group_history(self, conversation_id: int) -> bool:
        """删除群聊向量库"""
        try:
            collection_name = self._get_group_collection_name(conversation_id)
            vector_store = Chroma(
                client=None,
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            vector_store.delete_collection()
            return True
        except Exception as e:
            print(f"Error deleting group history: {e}")
            return False


# 全局实例
rag_service = RAGService()
