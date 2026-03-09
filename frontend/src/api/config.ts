import type { APIConfig } from '../types';

const API_CONFIG_KEY = 'claude_dev_api_config';

// 默认配置
const defaultConfig: APIConfig = {
  api_key: '',
  base_url: 'https://api.openai.com/v1',
  model_name: 'gpt-4-turbo-preview'
};

// 获取保存的配置
export function getAPIConfig(): APIConfig {
  try {
    const saved = localStorage.getItem(API_CONFIG_KEY);
    if (saved) {
      return { ...defaultConfig, ...JSON.parse(saved) };
    }
  } catch (e) {
    console.error('Failed to load API config:', e);
  }
  return defaultConfig;
}

// 保存配置
export function saveAPIConfig(config: APIConfig): void {
  try {
    localStorage.setItem(API_CONFIG_KEY, JSON.stringify(config));
  } catch (e) {
    console.error('Failed to save API config:', e);
  }
}

// 清除配置
export function clearAPIConfig(): void {
  localStorage.removeItem(API_CONFIG_KEY);
}

// 常用 API 端点
export const commonEndpoints = [
  { name: 'OpenAI', base_url: 'https://api.openai.com/v1' },
  { name: 'Azure OpenAI', base_url: '' }, // 用户需要填写
  { name: 'Anthropic (Claude)', base_url: 'https://api.minimaxi.com/anthropic' },
  { name: '通义千问', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
  { name: '硅基流动 (SiliconFlow)', base_url: 'https://api.siliconflow.cn/v1' },
  { name: '自定义', base_url: '' },
];

// 常用模型列表
export const commonModels = [
  'gpt-4-turbo-preview',
  'gpt-4',
  'gpt-3.5-turbo',
  'claude-3-opus-20240229',
  'claude-3-sonnet-20240229',
  'claude-3-haiku-20240307',
  'qwen-turbo',
  'qwen-plus',
  'qwen-max',
  'DeepSeek-V2-Chat',
];
