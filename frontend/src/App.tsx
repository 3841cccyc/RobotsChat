import { useState, useEffect, useCallback } from 'react';
import type { Bot, BotCreate, Conversation, Message, User, ViewMode, Group } from './types';
import { botApi, chatApi, groupChatApi, documentApi, userApi, groupApi } from './api';
import { getAPIConfig } from './api/config';
import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { GroupChatPanel } from './components/GroupChatPanel';
import { BotModal } from './components/BotModal';
import { SettingsPanel } from './components/SettingsPanel';
import { GroupModal, GroupList } from './components/GroupModal';

function App() {
  // 状态管理
  const [bots, setBots] = useState<Bot[]>([]);
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('chat');
  
  // 单独聊天状态
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [useDocs, setUseDocs] = useState(false);
  
  // 群聊状态
  const [selectedBotIds, setSelectedBotIds] = useState<number[]>([]);
  const [groupMessages, setGroupMessages] = useState<any[]>([]);
  const [isGroupStarted, setIsGroupStarted] = useState(false);
  const [groupConversationId, setGroupConversationId] = useState<number | null>(null);
  const [userName, setUserName] = useState('用户');
  
  // 自动聊天状态
  const [isAutoChatComplete, setIsAutoChatComplete] = useState(false);
  const [autoRounds, setAutoRounds] = useState(3);
  
  // 用户状态
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  
  // 弹窗状态
  const [isBotModalOpen, setIsBotModalOpen] = useState(false);
  const [editingBot, setEditingBot] = useState<Bot | null>(null);
  
  // 群组状态
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);

  // 加载机器人列表
  const loadBots = useCallback(async () => {
    try {
      const data = await botApi.getAll();
      setBots(data);
    } catch (error) {
      console.error('加载机器人失败:', error);
    }
  }, []);

  // 加载用户列表
  const loadUsers = useCallback(async () => {
    try {
      const data = await userApi.getAll();
      setUsers(data);
      if (data.length > 0) {
        setCurrentUser(data[0]);
        setUserName(data[0].name);
      }
    } catch (error) {
      console.error('加载用户失败:', error);
    }
  }, []);

  // 加载群组列表
  const loadGroups = useCallback(async () => {
    try {
      const data = await groupApi.getAll();
      setGroups(data);
    } catch (error) {
      console.error('加载群组失败:', error);
    }
  }, []);

  // 加载对话
  const loadConversations = useCallback(async (botId: number) => {
    try {
      const data = await botApi.getConversations(botId);
      setConversations(data);
    } catch (error) {
      console.error('加载对话失败:', error);
    }
  }, []);

  // 加载消息
  const loadMessages = useCallback(async (conversationId: number) => {
    try {
      const data = await chatApi.getMessages(conversationId);
      setMessages(data);
    } catch (error) {
      console.error('加载消息失败:', error);
    }
  }, []);

  // 初始化
  useEffect(() => {
    loadBots();
    loadUsers();
    loadGroups();
  }, [loadBots, loadUsers, loadGroups]);

  // 当选择机器人时加载对话
  useEffect(() => {
    if (selectedBot) {
      loadConversations(selectedBot.id);
      setMessages([]);
      setCurrentConversationId(null);
    }
  }, [selectedBot, loadConversations]);

  // 当选择对话时加载消息
  useEffect(() => {
    if (currentConversationId) {
      loadMessages(currentConversationId);
    }
  }, [currentConversationId, loadMessages]);

  // 创建机器人
  const handleCreateBot = async (bot: BotCreate) => {
    try {
      const newBot = await botApi.create(bot);
      setBots([...bots, newBot]);
      setIsBotModalOpen(false);
      setEditingBot(null);
    } catch (error) {
      console.error('创建机器人失败:', error);
      alert('创建机器人失败');
    }
  };

  // 删除机器人
  const handleDeleteBot = async (botId: number) => {
    if (!confirm('确定要删除这个机器人吗？')) return;
    try {
      await botApi.delete(botId);
      setBots(bots.filter(b => b.id !== botId));
      if (selectedBot?.id === botId) {
        setSelectedBot(null);
      }
    } catch (error) {
      console.error('删除机器人失败:', error);
    }
  };

  // 发送消息
  const handleSendMessage = async (content: string) => {
    if (!selectedBot) return;
    
    setIsLoading(true);
    try {
      // 获取 API 配置
      const apiConfig = getAPIConfig();
      console.log("[DEBUG] 发送消息, apiConfig:", apiConfig);
      
      const response = await chatApi.send({
        bot_id: selectedBot.id,
        message: content,
        conversation_id: currentConversationId || undefined,
        use_docs: useDocs,
        api_config: apiConfig,
      });
      
      // 加载最新消息
      const newMessages = await chatApi.getMessages(response.conversation_id);
      setMessages(newMessages);
      setCurrentConversationId(response.conversation_id);
      
      // 刷新对话列表
      loadConversations(selectedBot.id);
    } catch (error: any) {
      console.error('发送消息失败:', error);
      const errorMsg = error?.message || error?.detail || JSON.stringify(error) || '未知错误';
      alert('发送消息失败: ' + errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  // 新建对话
  const handleNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(null);
  };

  // 选择对话
  const handleSelectConversation = (id: number) => {
    setCurrentConversationId(id);
  };

  // 上传文档
  const handleUploadDocument = async (file: File) => {
    if (!selectedBot) return;
    try {
      await documentApi.upload(selectedBot.id, file);
      alert('文档上传成功');
    } catch (error) {
      console.error('上传文档失败:', error);
      alert('上传文档失败');
    }
  };

  // 群聊 - 切换机器人选择
  const handleToggleBot = (botId: number) => {
    if (selectedBotIds.includes(botId)) {
      setSelectedBotIds(selectedBotIds.filter(id => id !== botId));
    } else {
      setSelectedBotIds([...selectedBotIds, botId]);
    }
  };

  // 群聊 - 开始（使用流式）
  const handleStartGroupChat = async () => {
    if (selectedBotIds.length < 2) return;
    
    setIsLoading(true);
    setGroupMessages([]);
    
    // 用于追踪每个机器人的累积内容（用于覆盖式渲染）
    const botContents: Record<string, string> = {};
    
    try {
      const response = await groupChatApi.startStream({
        bot_ids: selectedBotIds,
        user_id: currentUser?.id,
        user_name: userName,
        topic: '群聊',
        include_docs: false,
      }, (data) => {
        console.log("[DEBUG] 流式数据:", data);
        
        if (data.type === 'user_message') {
          setGroupMessages(prev => [...prev, {
            role: 'user',
            content: data.content,
            sender_name: data.sender_name
          }]);
        } else if (data.type === 'bot_start') {
          // 初始化该机器人的累积内容
          botContents[data.bot_name] = '';
          // 新机器人开始回复
          setGroupMessages(prev => [...prev, {
            role: 'assistant',
            content: '',
            sender_name: data.bot_name,
            bot_id: data.bot_id,
            isStreaming: true
          }]);
        } else if (data.type === 'chunk') {
          // 覆盖式渲染：累积内容并直接替换
          botContents[data.bot_name] = (botContents[data.bot_name] || '') + data.content;
          const newContent = botContents[data.bot_name];
          
          setGroupMessages(prev => {
            const newMsgs = [...prev];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.isStreaming && lastMsg.sender_name === data.bot_name) {
              // 直接用新内容覆盖，而不是追加
              lastMsg.content = newContent;
            }
            return newMsgs;
          });
        } else if (data.type === 'bot_done') {
          // 机器人回复完成
          setGroupMessages(prev => {
            const newMsgs = [...prev];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.isStreaming) {
              lastMsg.isStreaming = false;
            }
            return newMsgs;
          });
        } else if (data.type === 'done') {
          setGroupConversationId(data.conversation_id);
          setIsGroupStarted(true);
        }
      });
    } catch (error) {
      console.error('启动群聊失败:', error);
      alert('启动群聊失败: ' + String(error));
    } finally {
      setIsLoading(false);
    }
  };

  // 群聊 - 发送消息（使用流式）
  const handleGroupSendMessage = async (content: string) => {
    if (!groupConversationId) return;
    
    setIsLoading(true);
    
    // 用于追踪每个机器人的累积内容（用于覆盖式渲染）
    const botContents: Record<string, string> = {};
    
    try {
      await groupChatApi.sendMessageStream({
        conversation_id: groupConversationId,
        user_name: userName,
        message: content,
        bot_ids: selectedBotIds,
        include_docs: false,
      }, (data) => {
        console.log("[DEBUG] 流式消息数据:", data);
        
        if (data.type === 'user_message') {
          setGroupMessages(prev => [...prev, {
            role: 'user',
            content: data.content,
            sender_name: data.sender_name
          }]);
        } else if (data.type === 'bot_start') {
          // 初始化该机器人的累积内容
          botContents[data.bot_name] = '';
          setGroupMessages(prev => [...prev, {
            role: 'assistant',
            content: '',
            sender_name: data.bot_name,
            bot_id: data.bot_id,
            isStreaming: true
          }]);
        } else if (data.type === 'chunk') {
          // 覆盖式渲染：累积内容并直接替换
          botContents[data.bot_name] = (botContents[data.bot_name] || '') + data.content;
          const newContent = botContents[data.bot_name];
          
          setGroupMessages(prev => {
            const newMsgs = [...prev];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.isStreaming && lastMsg.sender_name === data.bot_name) {
              // 直接用新内容覆盖，而不是追加
              lastMsg.content = newContent;
            }
            return newMsgs;
          });
        } else if (data.type === 'bot_done') {
          setGroupMessages(prev => {
            const newMsgs = [...prev];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.isStreaming) {
              lastMsg.isStreaming = false;
            }
            return newMsgs;
          });
        }
      });
    } catch (error) {
      console.error('发送群聊消息失败:', error);
      alert('发送消息失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 自动聊天 - 启动
  const handleStartAutoChat = async () => {
    if (!groupConversationId || selectedBotIds.length < 2) {
      alert('请确保已选择至少2个机器人');
      return;
    }
    
    console.log("[DEBUG] 开始自动聊天, conversationId:", groupConversationId, "botIds:", selectedBotIds, "rounds:", autoRounds);
    
    setIsLoading(true);
    setIsAutoChatComplete(false);
    
    // 用于追踪每个机器人的累积内容
    const botContents: Record<string, string> = {};
    
    try {
      await groupChatApi.startAutoChat(
        groupConversationId,
        selectedBotIds,
        autoRounds,
        (data) => {
          console.log("[DEBUG] 自动聊天数据:", data);
          
          if (data.type === 'auto_start') {
            // 自动聊天开始
            console.log("开始自动聊天，共", data.rounds, "轮");
          } else if (data.type === 'bot_start') {
            // 机器人开始回复
            botContents[data.bot_name] = '';
            setGroupMessages(prev => [...prev, {
              role: 'assistant',
              content: '',
              sender_name: data.bot_name,
              bot_id: data.bot_id,
              isStreaming: true,
              round: data.round,
              isFinal: data.is_final
            }]);
          } else if (data.type === 'chunk') {
            // 流式内容片段 - 覆盖式渲染
            botContents[data.bot_name] = (botContents[data.bot_name] || '') + data.content;
            const newContent = botContents[data.bot_name];
            
            setGroupMessages(prev => {
              const newMsgs = [...prev];
              const lastMsg = newMsgs[newMsgs.length - 1];
              
              // 如果是拆分消息的后续部分，需要追加到当前消息
              if (data.part && lastMsg && lastMsg.sender_name === data.bot_name && lastMsg.isStreaming) {
                // 追加内容（使用换行分隔）
                const prefix = lastMsg.content ? '\n' : '';
                lastMsg.content = lastMsg.content + prefix + data.content;
              } else if (lastMsg && lastMsg.isStreaming && lastMsg.sender_name === data.bot_name) {
                // 普通流式更新 - 覆盖
                lastMsg.content = newContent;
              }
              return newMsgs;
            });
          } else if (data.type === 'bot_done') {
            // 机器人回复完成
            setGroupMessages(prev => {
              const newMsgs = [...prev];
              const lastMsg = newMsgs[newMsgs.length - 1];
              if (lastMsg && lastMsg.isStreaming) {
                lastMsg.isStreaming = false;
              }
              return newMsgs;
            });
          } else if (data.type === 'message_split') {
            // 消息拆分信号 - 标记当前消息为第一条完成
            setGroupMessages(prev => {
              const newMsgs = [...prev];
              const lastMsg = newMsgs[newMsgs.length - 1];
              if (lastMsg && lastMsg.isStreaming) {
                // 这是一个拆分点，标记已发送第一条
                lastMsg.isFirstPartDone = true;
              }
              return newMsgs;
            });
            console.log("[DEBUG] 消息将拆分为", data.total_parts, "条发送");
          } else if (data.type === 'auto_complete' || data.type === 'auto_stopped') {
            // 自动聊天完成或停止
            setIsAutoChatComplete(true);
            setIsLoading(false);  // 完成后立即解除加载状态
            if (data.message) {
              console.log("自动聊天状态:", data.message);
            }
          } else if (data.type === 'error') {
            console.error("自动聊天错误:", data.error);
            alert("自动聊天出错: " + data.error);
            setIsLoading(false);  // 错误时也要解除加载状态
          }
        }
      );
    } catch (error: any) {
      console.error('启动自动聊天失败:', error);
      alert('启动自动聊天失败: ' + (error?.message || String(error)));
      setIsLoading(false);  // 确保错误时也解除加载状态
    }
    // 注意：不再在这里设置 setIsLoading(false)，因为需要等待流完成
  };

  // 自动聊天 - 停止
  const handleStopAutoChat = async () => {
    if (!groupConversationId) return;
    
    try {
      await groupChatApi.stopAutoChat(groupConversationId);
      setIsAutoChatComplete(true);
      console.log("已发送停止自动聊天请求");
    } catch (error) {
      console.error('停止自动聊天失败:', error);
    }
  };

  // 保存用户设置
  const handleSaveUser = async (userData: Partial<User>) => {
    try {
      if (currentUser) {
        await userApi.update(currentUser.id, userData);
      } else {
        const newUser = await userApi.create(userData);
        setCurrentUser(newUser);
      }
      loadUsers();
      alert('设置已保存');
    } catch (error) {
      console.error('保存用户设置失败:', error);
      alert('保存失败');
    }
  };

  // 群组管理 - 打开创建弹窗
  const handleOpenCreateGroup = () => {
    setEditingGroup(null);
    setIsGroupModalOpen(true);
  };

  // 群组管理 - 打开编辑弹窗
  const handleEditGroup = (group: Group) => {
    setEditingGroup(group);
    setIsGroupModalOpen(true);
  };

  // 群组管理 - 删除群组
  const handleDeleteGroup = async (groupId: number) => {
    try {
      await groupApi.delete(groupId);
      loadGroups();
      if (selectedGroup?.id === groupId) {
        setSelectedGroup(null);
      }
    } catch (error) {
      console.error('删除群组失败:', error);
      alert('删除群组失败');
    }
  };

  // 群组管理 - 从群组开始聊天
  const handleStartChatFromGroup = async (group: Group) => {
    if (group.members.length < 2) {
      alert('群组至少需要2个成员才能开始群聊');
      return;
    }
    
    setIsLoading(true);
    try {
      // 创建群聊会话
      const conversation = await groupApi.createConversation(group.id, group.name);
      
      setSelectedBotIds(group.members.map(m => m.id));
      setSelectedGroup(group);
      setGroupConversationId(conversation.id);
      setGroupMessages([]);
      setIsGroupStarted(true);  // 标记已启动，等待用户发消息
      
      // 切换到群聊视图
      setViewMode('group-chat');
    } catch (error) {
      console.error('创建群聊会话失败:', error);
      alert('创建群聊会话失败');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen flex">
      {/* 侧边栏 */}
      <Sidebar
        bots={bots}
        selectedBot={selectedBot}
        viewMode={viewMode}
        onSelectBot={setSelectedBot}
        onViewModeChange={setViewMode}
        onCreateBot={() => {
          setEditingBot(null);
          setIsBotModalOpen(true);
        }}
        onDeleteBot={handleDeleteBot}
        groups={groups}
        selectedGroupId={selectedGroup?.id}
        onSelectGroup={handleStartChatFromGroup}
        onEditGroup={handleEditGroup}
        onDeleteGroup={handleDeleteGroup}
        onCreateGroup={handleOpenCreateGroup}
      />

      {/* 主内容区 */}
      {viewMode === 'chat' && (
        <ChatPanel
          bot={selectedBot}
          messages={messages}
          conversations={conversations}
          currentConversationId={currentConversationId}
          isLoading={isLoading}
          useDocs={useDocs}
          onSendMessage={handleSendMessage}
          onNewConversation={handleNewConversation}
          onSelectConversation={handleSelectConversation}
          onToggleDocs={() => setUseDocs(!useDocs)}
          onUploadDocument={handleUploadDocument}
        />
      )}

      {viewMode === 'group-chat' && (
        <GroupChatPanel
          bots={bots}
          selectedBotIds={selectedBotIds}
          userName={userName}
          messages={groupMessages}
          isLoading={isLoading}
          isStarted={isGroupStarted}
          conversationId={groupConversationId}
          onToggleBot={handleToggleBot}
          onStartChat={handleStartGroupChat}
          onSendMessage={handleGroupSendMessage}
          onUserNameChange={setUserName}
          // 自动聊天相关
          isAutoChatComplete={isAutoChatComplete}
          autoRounds={autoRounds}
          onAutoRoundsChange={setAutoRounds}
          onStartAutoChat={handleStartAutoChat}
          onStopAutoChat={handleStopAutoChat}
        />
      )}

      {viewMode === 'settings' && (
        <SettingsPanel
          users={users}
          currentUser={currentUser}
          onSaveUser={handleSaveUser}
        />
      )}

      {/* 机器人编辑弹窗 */}
      <BotModal
        bot={editingBot}
        isOpen={isBotModalOpen}
        onClose={() => {
          setIsBotModalOpen(false);
          setEditingBot(null);
        }}
        onSave={handleCreateBot}
      />

      {/* 群组管理弹窗 */}
      <GroupModal
        isOpen={isGroupModalOpen}
        group={editingGroup}
        bots={bots}
        onClose={() => {
          setIsGroupModalOpen(false);
          setEditingGroup(null);
        }}
        onSave={() => {
          loadGroups();
        }}
      />
    </div>
  );
}

export default App;
