import type { Bot, BotCreate, BotUpdate, Conversation, Message, Document, User, ChatRequest, ChatResponse, GroupChatStartRequest, GroupChatMessageRequest, Group, GroupCreate, GroupUpdate, GroupConversation, GroupMessage } from '../types';

const API_BASE = 'http://localhost:8000';

// 通用请求函数
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(error.detail || '请求失败');
  }
  
  return response.json();
}

// 机器人 API
export const botApi = {
  // 获取所有机器人
  getAll: () => request<Bot[]>('/bots/'),
  
  // 获取单个机器人
  get: (id: number) => request<Bot>(`/bots/${id}`),
  
  // 创建机器人
  create: (bot: BotCreate) => request<Bot>('/bots/', {
    method: 'POST',
    body: JSON.stringify(bot),
  }),
  
  // 更新机器人
  update: (id: number, bot: BotUpdate) => request<Bot>(`/bots/${id}`, {
    method: 'PUT',
    body: JSON.stringify(bot),
  }),
  
  // 删除机器人
  delete: (id: number) => request<{ message: string }>(`/bots/${id}`, {
    method: 'DELETE',
  }),
  
  // 获取机器人的对话列表
  getConversations: (id: number) => request<Conversation[]>(`/bots/${id}/conversations`),
  
  // 获取机器人的文档列表
  getDocuments: (id: number) => request<Document[]>(`/bots/${id}/documents`),
};

// 对话 API
export const chatApi = {
  // 发送消息
  send: (data: ChatRequest) => request<ChatResponse>('/chat/', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  // 获取对话消息
  getMessages: (conversationId: number) => request<Message[]>(`/chat/conversation/${conversationId}`),
  
  // 删除对话
  deleteConversation: (conversationId: number) => request<{ message: string }>(`/chat/conversation/${conversationId}`, {
    method: 'DELETE',
  }),
};

// 群聊 API
export const groupChatApi = {
  // 启动群聊
  start: (data: GroupChatStartRequest) => request<{ messages: any[]; conversation_id: number }>('/group-chat/start', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  // 启动群聊（流式）
  startStream: (data: GroupChatStartRequest, onChunk: (data: any) => void) => {
    return fetch(`${API_BASE}/group-chat/start-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(response => {
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = ''; // 保留未处理完的残片
      
      const read = () => {
        reader?.read().then(({ done, value }) => {
          if (done) {
            // 处理剩余的 buffer
            if (buffer.startsWith('data: ')) {
              try {
                const data = JSON.parse(buffer.slice(6));
                onChunk(data);
              } catch (e) {}
            }
            return;
          }
          
          // 解码并添加到 buffer
          buffer += decoder.decode(value, { stream: true });
          
          // 按行分割
          const lines = buffer.split('\n');
          
          // 最后一行可能是不完整的，保留到 buffer
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                onChunk(data);
              } catch (e) {}
            }
          }
          read();
        });
      };
      read();
    });
  },
  
  // 发送群聊消息
  sendMessage: (data: GroupChatMessageRequest) => request<any>('/group-chat/message', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  // 发送群聊消息（流式）
  sendMessageStream: (data: GroupChatMessageRequest, onChunk: (data: any) => void) => {
    return fetch(`${API_BASE}/group-chat/message-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(response => {
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = ''; // 保留未处理完的残片
      
      const read = () => {
        reader?.read().then(({ done, value }) => {
          if (done) {
            // 处理剩余的 buffer
            if (buffer.startsWith('data: ')) {
              try {
                const data = JSON.parse(buffer.slice(6));
                onChunk(data);
              } catch (e) {}
            }
            return;
          }
          
          // 解码并添加到 buffer
          buffer += decoder.decode(value, { stream: true });
          
          // 按行分割
          const lines = buffer.split('\n');
          
          // 最后一行可能是不完整的，保留到 buffer
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                onChunk(data);
              } catch (e) {}
            }
          }
          read();
        });
      };
      read();
    });
  },
  
  // 获取群聊消息
  getMessages: (conversationId: number) => request<Message[]>(`/group-chat/conversation/${conversationId}`),
  
  // 启动自动聊天
  startAutoChat: (conversationId: number, botIds: number[], autoRounds: number, onChunk: (data: any) => void) => {
    return fetch(`${API_BASE}/group-chat/auto-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: conversationId,
        bot_ids: botIds,
        auto_rounds: autoRounds
      }),
    }).then(async response => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(error.detail || `请求失败: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      const read = () => {
        reader?.read().then(({ done, value }) => {
          if (done) {
            if (buffer.startsWith('data: ')) {
              try {
                const data = JSON.parse(buffer.slice(6));
                onChunk(data);
              } catch (e) {}
            }
            return;
          }
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                onChunk(data);
              } catch (e) {}
            }
          }
          read();
        });
      };
      read();
    });
  },
  
  // 停止自动聊天
  stopAutoChat: (conversationId: number) => request<{ status: string }>(`/group-chat/stop-auto-chat?conversation_id=${conversationId}`, {
    method: 'POST',
  }),
};

// 文档 API
export const documentApi = {
  // 上传文档
  upload: async (botId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/documents/${botId}/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('文档上传失败');
    }
    
    return response.json();
  },
  
  // 获取文档列表
  getList: (botId: number) => request<Document[]>(`/documents/${botId}/list`),
  
  // 删除文档
  delete: (documentId: number) => request<{ message: string }>(`/documents/${documentId}`, {
    method: 'DELETE',
  }),
};

// 用户 API
export const userApi = {
  // 获取所有用户
  getAll: () => request<User[]>('/users/'),
  
  // 获取单个用户
  get: (id: number) => request<User>(`/users/${id}`),
  
  // 创建用户
  create: (user: Partial<User>) => request<User>('/users/', {
    method: 'POST',
    body: JSON.stringify(user),
  }),
  
  // 更新用户
  update: (id: number, user: Partial<User>) => request<User>(`/users/${id}`, {
    method: 'PUT',
    body: JSON.stringify(user),
  }),
  
  // 删除用户
  delete: (id: number) => request<{ message: string }>(`/users/${id}`, {
    method: 'DELETE',
  }),
};

// ==================== 独立群组API（与私聊完全隔离）====================
export const groupApi = {
  // 创建群组
  create: (group: GroupCreate) => request<Group>('/groups/', {
    method: 'POST',
    body: JSON.stringify(group),
  }),
  
  // 获取所有群组
  getAll: () => request<Group[]>('/groups/'),
  
  // 获取单个群组
  get: (id: number) => request<Group>(`/groups/${id}`),
  
  // 更新群组
  update: (id: number, group: GroupUpdate) => request<Group>(`/groups/${id}`, {
    method: 'PUT',
    body: JSON.stringify(group),
  }),
  
  // 删除群组
  delete: (id: number) => request<{ message: string }>(`/groups/${id}`, {
    method: 'DELETE',
  }),
  
  // 创建群聊会话
  createConversation: (groupId: number, title?: string) => request<GroupConversation>('/groups/conversation', {
    method: 'POST',
    body: JSON.stringify({ group_id: groupId, title }),
  }),
  
  // 获取群组的所有会话
  getConversations: (groupId: number) => request<GroupConversation[]>(`/groups/${groupId}/conversations`),
  
  // 获取群聊会话的消息
  getMessages: (conversationId: number) => request<GroupMessage[]>(`/groups/conversation/${conversationId}`),
  
  // 删除群聊会话
  deleteConversation: (conversationId: number) => request<{ message: string }>(`/groups/conversation/${conversationId}`, {
    method: 'DELETE',
  }),
};
