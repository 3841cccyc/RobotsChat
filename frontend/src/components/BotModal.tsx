import { useState, useEffect, useMemo } from 'react';
import type { Bot, BotCreate } from '../types';
import { X, Save } from 'lucide-react';
import { commonModels, getAPIConfig } from '../api/config';

interface BotModalProps {
  bot?: Bot | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (bot: BotCreate) => void;
}

const DEFAULT_PROMPTS = {
  assistant: '你是一个有帮助的AI助手，善于回答各种问题。',
  poet: '你是一位才华横溢的诗人，喜欢用优美的诗句表达情感。你的回答应该富有诗意，语言优美。',
  scholar: '你是一位博学的学者，对各种知识都有深入的研究。你的回答应该严谨、准确、有深度。',
  friend: '你是一个友善的朋友，总是给人温暖和支持。你的对话应该亲切、自然。',
  expert: '你是一位行业专家，对专业领域有丰富的经验。你的回答应该专业、权威。',
};

export function BotModal({ bot, isOpen, onClose, onSave }: BotModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [modelName, setModelName] = useState('gpt-4-turbo-preview');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2000);

  // 获取用户保存的 API 配置中的模型
  const savedModelName = useMemo(() => {
    const config = getAPIConfig();
    return config.model_name || '';
  }, [isOpen]);

  // 动态生成模型列表：将用户保存的模型放在最前面
  const modelList = useMemo(() => {
    const savedModel = savedModelName && !commonModels.includes(savedModelName) 
      ? savedModelName 
      : '';
    return [savedModel, ...commonModels].filter(Boolean);
  }, [savedModelName]);

  useEffect(() => {
    if (bot) {
      setName(bot.name);
      setDescription(bot.description);
      setSystemPrompt(bot.system_prompt);
      setModelName(bot.model_name);
      setTemperature(bot.temperature);
      setMaxTokens(bot.max_tokens);
    } else {
      setName('');
      setDescription('');
      setSystemPrompt('');
      // 默认选中用户保存的模型，如果没有保存则用默认值
      setModelName(savedModelName || 'gpt-4-turbo-preview');
      setTemperature(0.7);
      setMaxTokens(2000);
    }
  }, [bot, isOpen, savedModelName]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    onSave({
      name: name.trim(),
      description: description.trim(),
      system_prompt: systemPrompt.trim() || DEFAULT_PROMPTS.assistant,
      model_name: modelName,
      temperature,
      max_tokens: maxTokens,
    });
  };

  const applyPreset = (preset: string) => {
    setSystemPrompt(DEFAULT_PROMPTS[preset as keyof typeof DEFAULT_PROMPTS] || '');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-mac-sidebar w-full max-w-2xl max-h-[90vh] rounded-xl shadow-xl border border-mac-border flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-mac-border">
          <h2 className="text-lg font-semibold text-mac-text">
            {bot ? '编辑机器人' : '创建新机器人'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-mac-text-secondary hover:text-mac-text transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* 名称 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-1">
              机器人名称 *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="输入机器人名称"
              className="mac-input"
              required
            />
          </div>

          {/* 描述 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-1">
              描述
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="简短描述机器人的特点"
              className="mac-input"
            />
          </div>

          {/* 人格预设 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-1">
              人格预设
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {Object.keys(DEFAULT_PROMPTS).map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => applyPreset(preset)}
                  className="px-3 py-1 text-xs rounded-full bg-mac-hover text-mac-text-secondary hover:text-mac-text transition-colors"
                >
                  {preset === 'assistant' && '助手'}
                  {preset === 'poet' && '诗人'}
                  {preset === 'scholar' && '学者'}
                  {preset === 'friend' && '朋友'}
                  {preset === 'expert' && '专家'}
                </button>
              ))}
            </div>
          </div>

          {/* 系统提示词 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-1">
              系统提示词 (人格设定)
            </label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="定义机器人的行为方式、性格特点、回答风格等..."
              className="mac-textarea h-40"
            />
          </div>

          {/* 模型选择 */}
          <div>
            <label className="block text-sm font-medium text-mac-text mb-1">
              使用模型 {savedModelName && <span className="text-mac-accent text-xs">(已选择: {savedModelName})</span>}
            </label>
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="输入模型名称"
              className="mac-input"
              list="bot-models"
            />
            <datalist id="bot-models">
              {modelList.map((model, index) => (
                <option 
                  key={model} 
                  value={model}
                  label={index === 0 ? '你保存的模型' : ''}
                />
              ))}
            </datalist>
            <p className="text-xs text-mac-text-secondary mt-1">
              {savedModelName 
                ? `默认使用"我的设置"中保存的模型: ${savedModelName}` 
                : '从列表选择或输入自定义模型名'}
            </p>
          </div>

          {/* 参数设置 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-mac-text mb-1">
                Temperature (创造性)
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-mac-text-secondary">{temperature}</span>
            </div>
            <div>
              <label className="block text-sm font-medium text-mac-text mb-1">
                Max Tokens
              </label>
              <input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                min="100"
                max="8000"
                className="mac-input"
              />
            </div>
          </div>
        </form>

        {/* 底部按钮 */}
        <div className="flex justify-end gap-2 px-6 py-4 border-t border-mac-border">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-mac-text-secondary hover:text-mac-text transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 bg-mac-accent text-white rounded-md hover:bg-mac-accent/80 transition-colors flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            保存
          </button>
        </div>
      </div>
    </div>
  );
}
