import { useState, useEffect } from 'react';
import type { Bot, Group, GroupCreate, GroupUpdate } from '../types';
import { groupApi } from '../api';
import { X, Plus, Settings, Trash2, Users, MessageCircle, Play } from 'lucide-react';

interface GroupModalProps {
  isOpen: boolean;
  group?: Group | null;
  bots: Bot[];
  onClose: () => void;
  onSave: () => void;
}

const ACTIVATION_STRATEGIES = [
  { value: 0, label: '自然顺序', description: '根据提及和活跃度自动激活' },
  { value: 1, label: '列表顺序', description: '按照成员列表顺序依次激活' },
  { value: 2, label: '池化激活', description: '优先让未发言的角色激活' },
  { value: 3, label: '手动激活', description: '完全随机选择发言角色' },
];

const GENERATION_MODES = [
  { value: 0, label: '轮换模式', description: '每次只生成一个角色的回复' },
  { value: 1, label: '追加模式', description: '将所有角色卡片合并为一个上下文' },
  { value: 2, label: '包含禁用', description: '包含被禁用的成员角色卡' },
];

export function GroupModal({ isOpen, group, bots, onClose, onSave }: GroupModalProps) {
  const [name, setName] = useState('');
  const [selectedBotIds, setSelectedBotIds] = useState<number[]>([]);
  const [allowSelfResponses, setAllowSelfResponses] = useState(false);
  const [activationStrategy, setActivationStrategy] = useState(0);
  const [generationMode, setGenerationMode] = useState(0);
  const [autoModeDelay, setAutoModeDelay] = useState(5);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (group) {
      setName(group.name);
      setSelectedBotIds(group.members.map(m => m.id));
      setAllowSelfResponses(group.allow_self_responses);
      setActivationStrategy(group.activation_strategy);
      setGenerationMode(group.generation_mode);
      setAutoModeDelay(group.auto_mode_delay);
    } else {
      setName('');
      setSelectedBotIds([]);
      setAllowSelfResponses(false);
      setActivationStrategy(0);
      setGenerationMode(0);
      setAutoModeDelay(5);
    }
  }, [group, isOpen]);

  const handleToggleBot = (botId: number) => {
    if (selectedBotIds.includes(botId)) {
      setSelectedBotIds(selectedBotIds.filter(id => id !== botId));
    } else {
      setSelectedBotIds([...selectedBotIds, botId]);
    }
  };

  const handleSave = async () => {
    if (!name.trim()) {
      alert('请输入群组名称');
      return;
    }
    if (selectedBotIds.length < 2) {
      alert('请至少选择2个机器人');
      return;
    }

    setIsSaving(true);
    try {
      const members = selectedBotIds.map((botId, index) => ({
        bot_id: botId,
        order_index: index,
      }));

      if (group) {
        // 更新群组
        const updateData: GroupUpdate = {
          name,
          allow_self_responses: allowSelfResponses,
          activation_strategy: activationStrategy,
          generation_mode: generationMode,
          auto_mode_delay: autoModeDelay,
          members,
        };
        await groupApi.update(group.id, updateData);
      } else {
        // 创建群组
        const createData: GroupCreate = {
          name,
          allow_self_responses: allowSelfResponses,
          activation_strategy: activationStrategy,
          generation_mode: generationMode,
          auto_mode_delay: autoModeDelay,
          members,
        };
        await groupApi.create(createData);
      }
      onSave();
      onClose();
    } catch (error) {
      console.error('保存群组失败:', error);
      alert('保存群组失败: ' + String(error));
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-mac-bg border border-mac-border rounded-xl w-[600px] max-h-[80vh] overflow-hidden flex flex-col">
        {/* 标题 */}
        <div className="px-6 py-4 border-b border-mac-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-mac-text">
            {group ? '编辑群组' : '创建群组'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-mac-hover rounded-md transition-colors"
          >
            <X className="w-5 h-5 text-mac-text-secondary" />
          </button>
        </div>

        {/* 内容 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* 群组名称 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-2">
              群组名称
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="输入群组名称"
              className="mac-input w-full"
            />
          </div>

          {/* 选择成员 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-2">
              成员 ({selectedBotIds.length}个)
            </label>
            <div className="flex flex-wrap gap-2">
              {bots.map((bot) => (
                <button
                  key={bot.id}
                  onClick={() => handleToggleBot(bot.id)}
                  className={`px-3 py-2 rounded-lg flex items-center gap-2 transition-colors ${
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
            {bots.length === 0 && (
              <p className="text-sm text-mac-text-secondary mt-2">
                暂无机器人，请先创建机器人
              </p>
            )}
          </div>

          {/* 激活策略 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-2">
              激活策略
            </label>
            <div className="grid grid-cols-2 gap-2">
              {ACTIVATION_STRATEGIES.map((strategy) => (
                <button
                  key={strategy.value}
                  onClick={() => setActivationStrategy(strategy.value)}
                  className={`p-3 rounded-lg text-left transition-colors ${
                    activationStrategy === strategy.value
                      ? 'bg-mac-accent text-white'
                      : 'bg-mac-hover text-mac-text hover:bg-mac-border'
                  }`}
                >
                  <div className="font-medium">{strategy.label}</div>
                  <div className={`text-xs ${
                    activationStrategy === strategy.value
                      ? 'text-white/70'
                      : 'text-mac-text-secondary'
                  }`}>
                    {strategy.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* 生成模式 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-2">
              生成模式
            </label>
            <div className="grid grid-cols-3 gap-2">
              {GENERATION_MODES.map((mode) => (
                <button
                  key={mode.value}
                  onClick={() => setGenerationMode(mode.value)}
                  className={`p-3 rounded-lg text-left transition-colors ${
                    generationMode === mode.value
                      ? 'bg-mac-accent text-white'
                      : 'bg-mac-hover text-mac-text hover:bg-mac-border'
                  }`}
                >
                  <div className="font-medium text-sm">{mode.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 自动模式延迟 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-2">
              自动模式延迟: {autoModeDelay}秒
            </label>
            <input
              type="range"
              min="1"
              max="30"
              value={autoModeDelay}
              onChange={(e) => setAutoModeDelay(Number(e.target.value))}
              className="w-full"
            />
          </div>

          {/* 允许自回复 */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="allowSelfResponses"
              checked={allowSelfResponses}
              onChange={(e) => setAllowSelfResponses(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="allowSelfResponses" className="text-sm text-mac-text">
              允许同一机器人连续回复
            </label>
          </div>
        </div>

        {/* 底部按钮 */}
        <div className="px-6 py-4 border-t border-mac-border flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-mac-text-secondary hover:text-mac-text transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || selectedBotIds.length < 2}
            className="px-4 py-2 bg-mac-accent text-white rounded-lg hover:bg-mac-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  );
}

// 群组列表组件
interface GroupListProps {
  groups: Group[];
  bots: Bot[];
  selectedGroupId: number | null;
  onSelectGroup: (group: Group) => void;
  onEditGroup: (group: Group) => void;
  onDeleteGroup: (groupId: number) => void;
  onStartChat: (group: Group) => void;
}

export function GroupList({
  groups,
  bots,
  selectedGroupId,
  onSelectGroup,
  onEditGroup,
  onDeleteGroup,
  onStartChat,
}: GroupListProps) {
  if (groups.length === 0) {
    return (
      <div className="text-center py-8 text-mac-text-secondary">
        <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>暂无群组</p>
        <p className="text-sm mt-1">点击上方按钮创建群组</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {groups.map((group) => (
        <div
          key={group.id}
          onClick={() => onSelectGroup(group)}
          className={`p-3 rounded-lg cursor-pointer transition-colors ${
            selectedGroupId === group.id
              ? 'bg-mac-accent text-white'
              : 'bg-mac-hover text-mac-text hover:bg-mac-border'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                selectedGroupId === group.id
                  ? 'bg-white/20'
                  : 'bg-mac-accent'
              }`}>
                <Users className="w-5 h-5" />
              </div>
              <div>
                <div className="font-medium">{group.name}</div>
                <div className={`text-xs ${
                  selectedGroupId === group.id
                    ? 'text-white/70'
                    : 'text-mac-text-secondary'
                }`}>
                  {group.members.length}个成员
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onStartChat(group);
                }}
                className={`p-2 rounded-md transition-colors ${
                  selectedGroupId === group.id
                    ? 'hover:bg-white/20'
                    : 'hover:bg-mac-accent/20 text-mac-accent'
                }`}
                title="开始群聊"
              >
                <Play className="w-4 h-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEditGroup(group);
                }}
                className={`p-2 rounded-md transition-colors ${
                  selectedGroupId === group.id
                    ? 'hover:bg-white/20'
                    : 'hover:bg-mac-hover'
                }`}
                title="编辑"
              >
                <Settings className="w-4 h-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm('确定要删除这个群组吗？')) {
                    onDeleteGroup(group.id);
                  }
                }}
                className={`p-2 rounded-md transition-colors ${
                  selectedGroupId === group.id
                    ? 'hover:bg-white/20'
                    : 'hover:bg-red-500/20 text-red-500'
                }`}
                title="删除"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
