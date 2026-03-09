from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# 机器人相关
class BotCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    system_prompt: Optional[str] = "你是一个有帮助的AI助手。"
    model_name: Optional[str] = "gpt-4-turbo-preview"
    avatar: Optional[str] = ""
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    talkativeness: Optional[float] = 0.5  # 活跃度（用于群聊激活策略）


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    avatar: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    talkativeness: Optional[float] = None


class BotResponse(BaseModel):
    id: int
    name: str
    description: str
    system_prompt: str
    model_name: str
    avatar: str
    temperature: float
    max_tokens: int
    talkativeness: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 对话相关
class ConversationCreate(BaseModel):
    bot_id: int
    title: Optional[str] = "新对话"


class ConversationResponse(BaseModel):
    id: int
    bot_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    learned_context: str

    class Config:
        from_attributes = True


# 消息相关
class MessageCreate(BaseModel):
    conversation_id: int
    role: str
    content: str
    sender_name: Optional[str] = ""


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    sender_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# API 配置
class APIConfig(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None


# 聊天请求
class ChatRequest(BaseModel):
    bot_id: int
    message: str
    conversation_id: Optional[int] = None
    use_docs: bool = False
    api_config: Optional[APIConfig] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: int
    message_id: int


# 文档相关
class DocumentResponse(BaseModel):
    id: int
    bot_id: int
    filename: str
    file_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# 用户相关
class UserCreate(BaseModel):
    name: str = "用户"
    description: Optional[str] = ""
    system_prompt: Optional[str] = "你是一个参与者，友善地参与讨论。"


class UserResponse(BaseModel):
    id: int
    name: str
    description: str
    system_prompt: str

    class Config:
        from_attributes = True


# 群聊相关
class GroupChatStartRequest(BaseModel):
    bot_ids: List[int]
    user_id: Optional[int] = None
    user_name: Optional[str] = "用户"
    user_prompt: Optional[str] = "请讨论一下人工智能的未来发展"
    topic: Optional[str] = ""
    include_docs: bool = False
    api_config: Optional[APIConfig] = None


class GroupChatMessageRequest(BaseModel):
    conversation_id: int
    user_name: str
    message: str
    bot_ids: List[int]
    include_docs: bool = False
    api_config: Optional[APIConfig] = None


class GroupChatResponse(BaseModel):
    messages: List[dict]
    conversation_id: int


# ==================== 独立群组系统（与私聊完全隔离）====================

class GroupMemberSchema(BaseModel):
    """群组成员Schema"""
    bot_id: int
    order_index: int = 0


class GroupMemberResponse(BaseModel):
    """群组成员响应"""
    id: int
    group_id: int
    bot_id: int
    order_index: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class GroupBotResponse(BaseModel):
    """群组中包含的机器人信息"""
    id: int
    name: str
    description: str
    avatar: str
    talkativeness: float


class GroupCreate(BaseModel):
    """创建群组请求"""
    name: str = "新群组"
    avatar_url: Optional[str] = ""
    allow_self_responses: bool = False
    activation_strategy: int = 0  # 0-自然顺序, 1-列表顺序, 2-池化激活, 3-手动激活
    generation_mode: int = 0  # 0-轮换模式, 1-追加模式, 2-包含禁用成员
    disabled_members: List[int] = []
    fav: bool = False
    auto_mode_delay: int = 5
    hide_muted_sprites: bool = False
    generation_mode_join_prefix: str = ""
    generation_mode_join_suffix: str = ""
    members: List[GroupMemberSchema] = []


class GroupUpdate(BaseModel):
    """更新群组请求"""
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    allow_self_responses: Optional[bool] = None
    activation_strategy: Optional[int] = None
    generation_mode: Optional[int] = None
    disabled_members: Optional[List[int]] = None
    fav: Optional[bool] = None
    auto_mode_delay: Optional[int] = None
    hide_muted_sprites: Optional[bool] = None
    generation_mode_join_prefix: Optional[str] = None
    generation_mode_join_suffix: Optional[str] = None
    members: Optional[List[GroupMemberSchema]] = None


class GroupResponse(BaseModel):
    """群组响应"""
    id: int
    name: str
    avatar_url: str
    allow_self_responses: bool
    activation_strategy: int
    generation_mode: int
    disabled_members: List[int]
    fav: bool
    auto_mode_delay: int
    hide_muted_sprites: bool
    generation_mode_join_prefix: str
    generation_mode_join_suffix: str
    created_at: datetime
    updated_at: datetime
    members: List[GroupBotResponse] = []
    
    class Config:
        from_attributes = True


class GroupConversationCreate(BaseModel):
    """创建群聊会话请求"""
    group_id: int
    title: Optional[str] = "群聊"


class GroupConversationResponse(BaseModel):
    """群聊会话响应"""
    id: int
    group_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GroupMessageCreate(BaseModel):
    """创建群聊消息请求"""
    conversation_id: int
    role: str
    content: str
    sender_name: Optional[str] = ""
    bot_id: Optional[int] = None


class GroupMessageResponse(BaseModel):
    """群聊消息响应"""
    id: int
    conversation_id: int
    role: str
    content: str
    sender_name: str
    bot_id: Optional[int]
    original_avatar: str
    created_at: datetime
    
    class Config:
        from_attributes = True
