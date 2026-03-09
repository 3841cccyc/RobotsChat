from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Bot(Base):
    """机器人模型"""
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), default="")
    system_prompt = Column(Text, default="你是一个有帮助的AI助手。")
    model_name = Column(String(100), default="gpt-4-turbo-preview")
    avatar = Column(String(500), default="")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    talkativeness = Column(Float, default=0.5)  # 活跃度（用于群聊激活策略）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    conversations = relationship("Conversation", back_populates="bot")
    documents = relationship("Document", back_populates="bot")
    group_messages = relationship("GroupMessage", back_populates="bot")


class GroupMember(Base):
    """
    群组成员关联表 - 多对多关系
    """
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    order_index = Column(Integer, default=0)  # 成员顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    group = relationship("Group", back_populates="members")
    bot = relationship("Bot")


class Conversation(Base):
    """对话会话模型 - 每个会话独立，互不影响"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    bot = relationship("Bot", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    learned_context = Column(Text, default="")  # 学习到的上下文


class Message(Base):
    """消息模型"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sender_name = Column(String(100), default="")  # 发送者名称（用于群聊）
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")


class Document(Base):
    """文档模型 - 用于RAG"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), default="text")
    content = Column(Text, default="")  # 提取的文本内容
    vector_store_id = Column(String(200), default="")  # ChromaDB中的ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    bot = relationship("Bot", back_populates="documents")


class User(Base):
    """用户配置模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="用户")
    description = Column(String(500), default="")
    system_prompt = Column(Text, default="你是一个参与者，友善地参与讨论。")
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== 群组相关模型（与私聊完全隔离）====================

class Group(Base):
    """
    群组模型 - 独立的群组系统，与私聊完全隔离
    """
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, default="新群组")
    avatar_url = Column(String(500), default="")  # 群组头像
    allow_self_responses = Column(Boolean, default=False)  # 是否允许同一机器人连续回复
    activation_strategy = Column(Integer, default=0)  # 激活策略: 0-自然顺序, 1-列表顺序, 2-池化激活, 3-手动激活, 4-随机激活, 5-相关激活
    generation_mode = Column(Integer, default=0)  # 生成模式: 0-轮换模式, 1-追加模式, 2-包含禁用成员
    disabled_members = Column(Text, default="[]")  # 禁用的成员ID列表（JSON数组）
    fav = Column(Boolean, default=False)  # 收藏标志
    auto_mode_delay = Column(Integer, default=5)  # 自动模式延迟（秒）
    hide_muted_sprites = Column(Boolean, default=False)  # 是否隐藏静音角色动画
    generation_mode_join_prefix = Column(String(50), default="")  # 生成模式连接前缀
    generation_mode_join_suffix = Column(String(50), default="")  # 生成模式连接后缀
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    conversations = relationship("GroupConversation", back_populates="group", order_by="GroupConversation.created_at")
    members = relationship("GroupMember", back_populates="group")


class GroupConversation(Base):
    """
    群聊会话模型 - 独立的群聊会话，与私聊完全隔离
    使用独立的表，不与私聊共享
    """
    __tablename__ = "group_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    title = Column(String(200), default="群聊")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    group = relationship("Group", back_populates="conversations")
    messages = relationship("GroupMessage", back_populates="conversation", order_by="GroupMessage.created_at")


class GroupMessage(Base):
    """
    群聊消息模型 - 独立的群聊消息，与私聊完全隔离
    """
    __tablename__ = "group_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("group_conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sender_name = Column(String(100), default="")  # 发送者名称
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=True)  # 发送的机器人ID（群聊用）
    original_avatar = Column(String(100), default="")  # 原始角色头像ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    conversation = relationship("GroupConversation", back_populates="messages")
    bot = relationship("Bot", back_populates="group_messages")
