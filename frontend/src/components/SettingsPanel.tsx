import { useState, useEffect } from 'react';
import type { User } from '../types';
import { Save, User as UserIcon } from 'lucide-react';

interface SettingsPanelProps {
  users: User[];
  currentUser: User | null;
  onSaveUser: (user: Partial<User>) => void;
}

export function SettingsPanel({ currentUser, onSaveUser }: SettingsPanelProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    if (currentUser) {
      setName(currentUser.name);
      setDescription(currentUser.description);
      setSystemPrompt(currentUser.system_prompt);
    } else {
      setName('用户');
      setDescription('');
      setSystemPrompt('你是一个友善的参与者，热情地参与讨论。');
    }
  }, [currentUser]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSaveUser({
      name: name.trim() || '用户',
      description: description.trim(),
      system_prompt: systemPrompt.trim(),
    });
    setSaveMessage('设置已保存');
    setTimeout(() => setSaveMessage(''), 2000);
  };

  return (
    <div className="flex-1 bg-mac-bg overflow-y-auto">
      <div className="max-w-2xl mx-auto p-6">
        <div className="flex items-center gap-3 mb-6">
          <UserIcon className="w-6 h-6 text-mac-accent" />
          <h2 className="text-xl font-semibold text-mac-text">我的设置</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 用户身份设置 */}
          <div className="bg-mac-sidebar rounded-lg p-6 border border-mac-border">
            <h3 className="text-lg font-medium text-mac-text mb-4">用户身份设置</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-mac-text mb-1">
                  显示名称
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="你在群聊中显示的名字"
                  className="mac-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-mac-text mb-1">
                  个人描述
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="简短描述你自己"
                  className="mac-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-mac-text mb-1">
                  参与群聊时的系统提示词
                </label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="定义你在群聊中的行为方式..."
                  className="mac-textarea h-32"
                />
              </div>
            </div>
          </div>

          {/* 使用说明 */}
          <div className="bg-mac-sidebar rounded-lg p-6 border border-mac-border">
            <h3 className="text-lg font-medium text-mac-text mb-4">使用说明</h3>
            <ul className="space-y-2 text-sm text-mac-text-secondary">
              <li>• <strong className="text-mac-text">单独聊</strong>：选择一个机器人进行一对一对话</li>
              <li>• <strong className="text-mac-text">群聊</strong>：让多个机器人互相聊天，你可以旁观或参与</li>
              <li>• <strong className="text-mac-text">文档模式</strong>：上传文档后，机器人可以理解文档内容</li>
              <li>• <strong className="text-mac-text">创建机器人</strong>：为每个机器人设定独特的人格和回答风格</li>
            </ul>
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-mac-accent text-white rounded-lg hover:bg-mac-accent/80 transition-colors flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            保存设置
          </button>
          
          {saveMessage && (
            <p className="text-sm text-green-400 text-center">{saveMessage}</p>
          )}
        </form>
      </div>
    </div>
  );
}
