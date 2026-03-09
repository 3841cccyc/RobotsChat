import { useState, useRef, useEffect } from 'react';
import type { Bot, Message } from '../types';
import { Send, Play, Loader2, User, Zap, Square } from 'lucide-react';

interface GroupChatPanelProps {
  bots: Bot[];
  selectedBotIds: number[];
  userName: string;
  messages: Message[];
  isLoading: boolean;
  isStarted: boolean;
  conversationId: number | null;
  onToggleBot: (botId: number) => void;
  onStartChat: () => void;
  onSendMessage: (message: string) => void;
  onUserNameChange: (name: string) => void;
  // 自动聊天相关
  isAutoChatComplete?: boolean;
  autoRounds?: number;
  onAutoRoundsChange?: (rounds: number) => void;
  onStartAutoChat?: () => void;
  onStopAutoChat?: () => void;
}

export function GroupChatPanel({
  bots,
  selectedBotIds,
  userName,
  messages,
  isLoading,
  isStarted,
  conversationId,
  onToggleBot,
  onStartChat,
  onSendMessage,
  onUserNameChange,
  isAutoChatComplete,
  autoRounds,
  onAutoRoundsChange,
  onStartAutoChat,
  onStopAutoChat,
}: GroupChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading && conversationId) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const selectedBots = bots.filter((b) => selectedBotIds.includes(b.id));

  return (
    <div className="flex-1 flex flex-col bg-mac-bg">
      {/* 顶部栏 */}
      <div className="h-14 px-4 border-b border-mac-border flex items-center justify-between bg-mac-sidebar">
        <div>
          <h2 className="text-sm font-medium text-mac-text">群聊模式</h2>
          <p className="text-xs text-mac-text-secondary">
            {selectedBots.length} 个机器人参与
          </p>
        </div>
        
        {isStarted && (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={userName}
              onChange={(e) => onUserNameChange(e.target.value)}
              placeholder="你的名字"
              className="mac-input w-32 text-sm"
            />
          </div>
        )}
      </div>

      {/* 机器人选择 */}
      {!isStarted && (
        <div className="p-4 border-b border-mac-border">
          <h3 className="text-sm font-medium text-mac-text mb-3">选择参与群聊的机器人</h3>
          <div className="flex flex-wrap gap-2">
            {bots.map((bot) => (
              <button
                key={bot.id}
                onClick={() => onToggleBot(bot.id)}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  selectedBotIds.includes(bot.id)
                    ? 'bg-mac-accent text-white'
                    : 'bg-mac-hover text-mac-text-secondary hover:text-mac-text'
                }`}
              >
                <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-xs">
                  {bot.name.charAt(0)}
                </div>
                {bot.name}
              </button>
            ))}
          </div>
          
          <button
            onClick={onStartChat}
            disabled={selectedBotIds.length < 2}
            className="mt-4 w-full py-3 bg-mac-accent text-white rounded-lg hover:bg-mac-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            <Play className="w-4 h-4" />
            开始群聊
          </button>
          
          {selectedBotIds.length < 2 && (
            <p className="text-xs text-mac-text-secondary text-center mt-2">
              请至少选择 2 个机器人
            </p>
          )}
        </div>
      )}

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!isStarted ? (
          <div className="text-center text-mac-text-secondary py-8">
            <p>选择机器人并开始群聊</p>
            <p className="text-sm mt-2">机器人将自动对话，你也可以参与</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3 ${msg.role === 'user' && msg.sender_name === userName ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-medium ${
                  msg.role === 'user'
                    ? msg.sender_name === userName
                      ? 'bg-mac-accent'
                      : 'bg-green-500'
                    : 'bg-mac-accent'
                }`}
              >
                {msg.role === 'user' ? <User className="w-4 h-4" /> : msg.sender_name?.charAt(0) || '?'}
              </div>
              <div
                className={`max-w-[70%] px-4 py-2 rounded-lg ${
                  msg.role === 'user'
                    ? msg.sender_name === userName
                      ? 'bg-mac-accent text-white'
                      : 'bg-green-500/20 text-mac-text'
                    : 'bg-mac-sidebar text-mac-text'
                }`}
              >
                <p className="text-xs text-mac-text-secondary mb-1">
                  {msg.sender_name || (msg.role === 'user' ? '用户' : '机器人')}
                </p>
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
              <p className="text-sm text-mac-text-secondary">正在生成回复...</p>
            </div>
          </div>
        )}
        
        {/* 显示正在输入的机器人 */}
        {messages.some(m => m.isStreaming) && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-mac-accent flex items-center justify-center text-sm">
              {messages.find(m => m.isStreaming)?.sender_name?.charAt(0) || '?'}
            </div>
            <div className="bg-mac-sidebar px-4 py-2 rounded-lg">
              <p className="text-xs text-mac-text-secondary mb-1">
                {messages.find(m => m.isStreaming)?.sender_name} 正在输入
              </p>
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-mac-accent rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                <span className="w-2 h-2 bg-mac-accent rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                <span className="w-2 h-2 bg-mac-accent rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      {isStarted && (
        <div className="p-4 border-t border-mac-border">
          {/* 自动聊天控制区域 */}
          <div className="mb-3 flex items-center gap-3 p-3 bg-mac-sidebar rounded-lg">
            <Zap className="w-4 h-4 text-mac-accent" />
            <span className="text-sm text-mac-text">自动聊天</span>
            
            {/* 轮数选择 */}
            <div className="flex items-center gap-1 ml-2">
              <span className="text-xs text-mac-text-secondary">轮数:</span>
              {[3, 4, 5].map((r) => (
                <button
                  key={r}
                  onClick={() => onAutoRoundsChange?.(r)}
                  disabled={isLoading}
                  className={`px-2 py-1 text-xs rounded ${
                    autoRounds === r
                      ? 'bg-mac-accent text-white'
                      : 'bg-mac-hover text-mac-text-secondary hover:text-mac-text'
                  } disabled:opacity-50`}
                >
                  {r}
                </button>
              ))}
            </div>
            
            {/* 开始/停止按钮 */}
            {isLoading ? (
              <button
                onClick={onStopAutoChat}
                className="ml-auto px-3 py-1.5 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 flex items-center gap-1"
              >
                <Square className="w-3 h-3" />
                停止
              </button>
            ) : isAutoChatComplete ? (
              <button
                onClick={onStartAutoChat}
                className="ml-auto px-3 py-1.5 bg-mac-accent text-white text-sm rounded-lg hover:bg-mac-accent/80 flex items-center gap-1"
              >
                <Zap className="w-3 h-3" />
                继续聊天
              </button>
            ) : (
              <button
                onClick={onStartAutoChat}
                disabled={selectedBotIds.length < 2}
                className="ml-auto px-3 py-1.5 bg-mac-accent text-white text-sm rounded-lg hover:bg-mac-accent/80 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <Zap className="w-3 h-3" />
                开始自动聊天
              </button>
            )}
            
            {isAutoChatComplete && (
              <span className="text-xs text-mac-text-secondary">
                (等待你的确认)
              </span>
            )}
          </div>
          
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`以 ${userName} 的身份发言...`}
              className="mac-input flex-1"
              disabled={isLoading}
            />
            
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 bg-mac-accent text-white rounded-md hover:bg-mac-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
