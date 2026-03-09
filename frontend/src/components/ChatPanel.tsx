import { useState, useRef, useEffect } from 'react';
import type { Bot, Message, Conversation } from '../types';
import { Send, Plus, FileText, Loader2 } from 'lucide-react';

interface ChatPanelProps {
  bot: Bot | null;
  messages: Message[];
  conversations: Conversation[];
  currentConversationId: number | null;
  isLoading: boolean;
  useDocs: boolean;
  onSendMessage: (message: string) => void;
  onNewConversation: () => void;
  onSelectConversation: (id: number) => void;
  onToggleDocs: () => void;
  onUploadDocument: (file: File) => void;
}

export function ChatPanel({
  bot,
  messages,
  conversations,
  currentConversationId,
  isLoading,
  useDocs,
  onSendMessage,
  onNewConversation,
  onSelectConversation,
  onToggleDocs,
  onUploadDocument,
}: ChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 自动滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadDocument(file);
      e.target.value = '';
    }
  };

  if (!bot) {
    return (
      <div className="flex-1 flex items-center justify-center bg-mac-bg">
        <div className="text-center text-mac-text-secondary">
          <p className="text-lg mb-2">选择一个机器人开始对话</p>
          <p className="text-sm">或创建新的机器人</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-mac-bg">
      {/* 顶部栏 */}
      <div className="h-14 px-4 border-b border-mac-border flex items-center justify-between bg-mac-sidebar">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-mac-accent/30 flex items-center justify-center text-sm font-medium">
            {bot.name.charAt(0)}
          </div>
          <div>
            <h2 className="text-sm font-medium text-mac-text">{bot.name}</h2>
            <p className="text-xs text-mac-text-secondary">{bot.model_name}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 文档开关 */}
          <button
            onClick={onToggleDocs}
            className={`px-3 py-1.5 rounded-md text-sm flex items-center gap-1 transition-colors ${
              useDocs
                ? 'bg-mac-accent text-white'
                : 'bg-mac-hover text-mac-text-secondary hover:text-mac-text'
            }`}
          >
            <FileText className="w-4 h-4" />
            文档模式
          </button>
          
          {/* 新建对话 */}
          <button
            onClick={onNewConversation}
            className="p-2 rounded-md text-mac-text-secondary hover:text-mac-text hover:bg-mac-hover transition-colors"
            title="新建对话"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 对话历史列表 */}
      {conversations.length > 0 && (
        <div className="px-4 py-2 border-b border-mac-border overflow-x-auto scrollbar-hide">
          <div className="flex gap-2">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`px-3 py-1 rounded-md text-sm whitespace-nowrap transition-colors ${
                  currentConversationId === conv.id
                    ? 'bg-mac-accent text-white'
                    : 'bg-mac-hover text-mac-text-secondary hover:text-mac-text'
                }`}
              >
                {conv.title || '新对话'}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-mac-text-secondary py-8">
            <p>和 {bot.name} 开始对话吧</p>
            <p className="text-sm mt-2">{bot.description || bot.system_prompt.slice(0, 100)}...</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-medium ${
                  msg.role === 'user'
                    ? 'bg-mac-accent/30'
                    : 'bg-mac-accent'
                }`}
              >
                {msg.role === 'user' ? '你' : bot.name.charAt(0)}
              </div>
              <div
                className={`max-w-[70%] px-4 py-2 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-mac-accent/20 text-mac-text'
                    : 'bg-mac-sidebar text-mac-text'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-mac-accent flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-mac-sidebar px-4 py-2 rounded-lg">
              <p className="text-sm text-mac-text-secondary">正在思考...</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="p-4 border-t border-mac-border">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`对 ${bot.name} 说...`}
            className="mac-input flex-1"
            disabled={isLoading}
          />
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
            accept=".pdf,.doc,.docx,.txt"
          />
          
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2 rounded-md text-mac-text-secondary hover:text-mac-text hover:bg-mac-hover transition-colors"
            title="上传文档"
          >
            <FileText className="w-5 h-5" />
          </button>
          
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-mac-accent text-white rounded-md hover:bg-mac-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
