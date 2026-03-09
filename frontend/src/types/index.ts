// 机器人类型
export interface Bot {
  id: number;
  name: string;
  description: string;
  system_prompt: string;
  model_name: string;
  avatar: string;
  temperature: number;
  max_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface BotCreate {
  name: string;
  description?: string;
  system_prompt?: string;
  model_name?: string;
  avatar?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface BotUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  model_name?: string;
  avatar?: string;
  temperature?: number;
  max_tokens?: number;
}

// 对话类型
export interface Conversation {
  id: number;
  bot_id: number;
  title: string;
  created_at: string;
  updated_at: string;
  learned_context: string;
}

// 消息类型
export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sender_name: string;
  created_at: string;
}

// 文档类型
export interface Document {
  id: number;
  bot_id: number;
  filename: string;
  file_type: string;
  created_at: string;
}

// 用户类型
export interface User {
  id: number;
  name: string;
  description: string;
  system_prompt: string;
}

// 聊天请求类型
export interface ChatRequest {
  bot_id: number;
  message: string;
  conversation_id?: number;
  use_docs: boolean;
  api_config?: APIConfig;
}

export interface ChatResponse {
  message: string;
  conversation_id: number;
  message_id: number;
}

// 群聊请求类型
export interface GroupChatStartRequest {
  bot_ids: number[];
  user_id?: number;
  user_name?: string;
  user_prompt?: string;
  topic?: string;
  include_docs: boolean;
  api_config?: APIConfig;
}

export interface GroupChatMessageRequest {
  conversation_id: number;
  user_name: string;
  message: string;
  bot_ids: number[];
  include_docs: boolean;
  api_config?: APIConfig;
}

// API 配置类型
export interface APIConfig {
  api_key?: string;
  base_url?: string;
  model_name?: string;
}

// 视图模式
export type ViewMode = 'chat' | 'group-chat' | 'settings';

// ==================== 独立群组系统类型（与私聊完全隔离）====================

// 群组成员
export interface GroupMember {
  bot_id: number;
  order_index: number;
}

// 群组中的机器人信息
export interface GroupBot {
  id: number;
  name: string;
  description: string;
  avatar: string;
  talkativeness: number;
}

// 创建群组请求
export interface GroupCreate {
  name: string;
  avatar_url?: string;
  allow_self_responses?: boolean;
  activation_strategy?: number;  // 0-自然顺序, 1-列表顺序, 2-池化激活, 3-手动激活
  generation_mode?: number;  // 0-轮换模式, 1-追加模式, 2-包含禁用成员
  disabled_members?: number[];
  fav?: boolean;
  auto_mode_delay?: number;
  hide_muted_sprites?: boolean;
  generation_mode_join_prefix?: string;
  generation_mode_join_suffix?: string;
  members?: GroupMember[];
}

// 更新群组请求
export interface GroupUpdate {
  name?: string;
  avatar_url?: string;
  allow_self_responses?: boolean;
  activation_strategy?: number;
  generation_mode?: number;
  disabled_members?: number[];
  fav?: boolean;
  auto_mode_delay?: number;
  hide_muted_sprites?: boolean;
  generation_mode_join_prefix?: string;
  generation_mode_join_suffix?: string;
  members?: GroupMember[];
}

// 群组响应
export interface Group {
  id: number;
  name: string;
  avatar_url: string;
  allow_self_responses: boolean;
  activation_strategy: number;
  generation_mode: number;
  disabled_members: number[];
  fav: boolean;
  auto_mode_delay: number;
  hide_muted_sprites: boolean;
  generation_mode_join_prefix: string;
  generation_mode_join_suffix: string;
  created_at: string;
  updated_at: string;
  members: GroupBot[];
}

// 群聊会话
export interface GroupConversation {
  id: number;
  group_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

// 群聊消息
export interface GroupMessage {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sender_name: string;
  bot_id?: number;
  original_avatar: string;
  created_at: string;
}
