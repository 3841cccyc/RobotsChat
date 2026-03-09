from anthropic import Anthropic
from app.config import settings
from typing import List, Dict, Any, AsyncGenerator
import os


class LLMService:
    """LLM 服务封装 - 使用 Anthropic SDK (MiniMax)"""
    
    def __init__(self):
        self.api_key = settings.minimax_api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.base_url = settings.minimax_base_url
        self.model = settings.minimax_model
        
    def _get_client(self) -> Anthropic:
        """获取 Anthropic 客户端"""
        return Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        learned_context: str = "",
    ) -> str:
        """单轮对话"""
        client = self._get_client()
        
        # 构建消息列表
        anthropic_messages = []
        
        # 添加历史消息
        for msg in messages:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 构建完整的系统提示词
        full_system = system_prompt
        if learned_context:
            full_system += f"\n\n【已学习的知识】:\n{learned_context}"
        
        # 调用模型
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=full_system if full_system else "You are a helpful assistant.",
            messages=anthropic_messages,
            temperature=temperature
        )
        
        # 提取文本内容
        return self._extract_text(response)
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        learned_context: str = "",
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        client = self._get_client()
        
        # 构建消息列表
        anthropic_messages = []
        
        # 添加历史消息
        for msg in messages:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 构建完整的系统提示词
        full_system = system_prompt
        if learned_context:
            full_system += f"\n\n【已学习的知识】:\n{learned_context}"
        
        # 添加防重复提示
        full_system += "\n\n【重要】: 请尽量不要重复之前说过的话，保持回复的多样性和新颖性。"
        
        # 调用模型（流式）
        try:
            with client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=full_system if full_system else "You are a helpful assistant.",
                messages=anthropic_messages,
                temperature=temperature
            ) as stream:
                for text_delta in stream.text_stream:
                    yield text_delta
        except Exception as e:
            print(f"[ERROR] LLM stream error: {e}")
            yield "抱歉，我遇到了一些问题。"
    
    async def chat_with_docs(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        docs_context: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        learned_context: str = "",
    ) -> str:
        """带文档上下文的对话"""
        client = self._get_client()
        
        # 构建消息列表
        anthropic_messages = []
        
        # 添加历史消息
        for msg in messages:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 构建完整的系统提示词
        full_system = system_prompt
        
        # 添加文档上下文
        if docs_context:
            full_system += f"\n\n【参考文档内容】:\n{docs_context}"
        
        # 添加学习到的上下文
        if learned_context:
            full_system += f"\n\n【已学习的知识】:\n{learned_context}"
        
        # 调用模型
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=full_system if full_system else "You are a helpful assistant.",
            messages=anthropic_messages,
            temperature=temperature
        )
        
        # 提取文本内容
        return self._extract_text(response)
    
    def _extract_text(self, response) -> str:
        """从响应中提取文本"""
        text_parts = []
        for block in response.content:
            if hasattr(block, 'text'):
                text_parts.append(block.text)
            elif isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
        return "\n".join(text_parts)


# 全局实例
llm_service = LLMService()
