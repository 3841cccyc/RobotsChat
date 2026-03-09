import type { Bot, ViewMode, Group } from '../types';
import { Plus, MessageCircle, Users, Settings, Trash2, Bot as BotIcon, Play, Edit } from 'lucide-react';

interface SidebarProps {
  bots: Bot[];
  selectedBot: Bot | null;
  viewMode: ViewMode;
  onSelectBot: (bot: Bot) => void;
  onViewModeChange: (mode: ViewMode) => void;
  onCreateBot: () => void;
  onDeleteBot: (botId: number) => void;
  groups?: Group[];
  selectedGroupId?: number | null;
  onSelectGroup?: (group: Group) => void;
  onEditGroup?: (group: Group) => void;
  onDeleteGroup?: (groupId: number) => void;
  onCreateGroup?: () => void;
}

export function Sidebar({
  bots,
  selectedBot,
  viewMode,
  onSelectBot,
  onViewModeChange,
  onCreateBot,
  onDeleteBot,
  groups = [],
  selectedGroupId = null,
  onSelectGroup,
  onEditGroup,
  onDeleteGroup,
  onCreateGroup,
}: SidebarProps) {
  return (
    <div className="w-64 h-full bg-mac-sidebar border-r border-mac-border flex flex-col">
      {/* 标题 */}
      <div className="p-4 border-b border-mac-border">
        <h1 className="text-lg font-semibold text-mac-text flex items-center gap-2">
          <BotIcon className="w-5 h-5" />
          机器人对话
        </h1>
      </div>

      {/* 导航标签 */}
      <div className="flex border-b border-mac-border">
        <button
          onClick={() => onViewModeChange('chat')}
          className={`flex-1 py-2 px-3 text-sm flex items-center justify-center gap-1 transition-colors ${
            viewMode === 'chat'
              ? 'text-mac-accent border-b-2 border-mac-accent'
              : 'text-mac-text-secondary hover:text-mac-text'
          }`}
        >
          <MessageCircle className="w-4 h-4" />
          单独聊
        </button>
        <button
          onClick={() => onViewModeChange('group-chat')}
          className={`flex-1 py-2 px-3 text-sm flex items-center justify-center gap-1 transition-colors ${
            viewMode === 'group-chat'
              ? 'text-mac-accent border-b-2 border-mac-accent'
              : 'text-mac-text-secondary hover:text-mac-text'
          }`}
        >
          <Users className="w-4 h-4" />
          群聊
        </button>
      </div>

      {/* 机器人列表 */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="text-xs text-mac-text-secondary px-2 py-1">机器人列表</div>
        {bots.map((bot) => (
          <div
            key={bot.id}
            className={`group flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors ${
              selectedBot?.id === bot.id && viewMode === 'chat'
                ? 'bg-mac-accent/20 text-mac-text'
                : 'hover:bg-mac-hover text-mac-text-secondary hover:text-mac-text'
            }`}
            onClick={() => {
              onSelectBot(bot);
              onViewModeChange('chat');
            }}
          >
            <div className="w-8 h-8 rounded-full bg-mac-accent/30 flex items-center justify-center text-sm font-medium">
              {bot.name.charAt(0)}
            </div>
            <span className="flex-1 truncate text-sm">{bot.name}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDeleteBot(bot.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}

        {/* 新建机器人按钮 */}
        <button
          onClick={onCreateBot}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-mac-text-secondary hover:text-mac-text hover:bg-mac-hover transition-colors mt-2"
        >
          <Plus className="w-4 h-4" />
          <span className="text-sm">新建机器人</span>
        </button>

        {/* 群组列表 - 仅在群聊模式显示 */}
        {viewMode === 'group-chat' && (
          <>
            <div className="text-xs text-mac-text-secondary px-2 py-1 mt-4">群组列表</div>
            {groups.map((group) => (
              <div
                key={group.id}
                className={`group flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors ${
                  selectedGroupId === group.id
                    ? 'bg-mac-accent/20 text-mac-text'
                    : 'hover:bg-mac-hover text-mac-text-secondary hover:text-mac-text'
                }`}
                onClick={() => onSelectGroup?.(group)}
              >
                <div className="w-8 h-8 rounded-full bg-mac-accent/30 flex items-center justify-center text-sm font-medium">
                  <Users className="w-4 h-4" />
                </div>
                <span className="flex-1 truncate text-sm">{group.name}</span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectGroup?.(group);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-green-400 transition-opacity"
                    title="开始群聊"
                  >
                    <Play className="w-3 h-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditGroup?.(group);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-blue-400 transition-opacity"
                    title="编辑"
                  >
                    <Edit className="w-3 h-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('确定要删除这个群组吗？')) {
                        onDeleteGroup?.(group.id);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                    title="删除"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
            <button
              onClick={onCreateGroup}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-mac-text-secondary hover:text-mac-text hover:bg-mac-hover transition-colors mt-2"
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm">新建群组</span>
            </button>
          </>
        )}
      </div>

      {/* 底部设置 */}
      <div className="p-2 border-t border-mac-border">
        <button
          onClick={() => onViewModeChange('settings')}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
            viewMode === 'settings'
              ? 'bg-mac-accent/20 text-mac-text'
              : 'text-mac-text-secondary hover:text-mac-text hover:bg-mac-hover'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span className="text-sm">我的设置</span>
        </button>
      </div>
    </div>
  );
}
