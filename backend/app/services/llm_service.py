from anthropic import Anthropic
from app.config import settings
from app.services.streaming_dedup import BufferedDeduplicator
from typing import List, Dict, Any, AsyncGenerator
import os
import asyncio
import re


class LLMService:
    """LLM 服务封装 - 使用 Anthropic SDK (MiniMax)"""

    def __init__(self):
        self.api_key = settings.minimax_api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.base_url = settings.minimax_base_url
        self.model = settings.minimax_model

    def _get_client(self) -> Anthropic:
        """获取 Anthropic 客户端"""
        return Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _deduplicate_text(self, text: str) -> str:
        """强力去重：去除文本中的重复内容（多轮迭代）"""
        if not text:
            return text

        original = text
        max_iterations = 15  # 增加迭代次数

        for iteration in range(max_iterations):
            prev_text = text

            # 1. 去除连续重复的字符（如 "啊啊啊" -> "啊"）
            text = re.sub(r'(.)\1{2,}', r'\1', text)

            # 2. 去除连续重复的词组（更激进）
            text = re.sub(r'(.{2,})\1{1,}', r'\1', text)

            # 3. 按行去重（去除完全相同的行）
            lines = text.split('\n')
            unique_lines = []
            seen = set()
            for line in lines:
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
                    unique_lines.append(line)
            text = '\n'.join(unique_lines)

            # 4. 去除句内重复段落（更激进）
            text = re.sub(r'(.{8,80})\1{1,}', r'\1', text)

            # 5. 去除连续重复的完整句子
            text = re.sub(r'([^。！？♪♫✨\n]{10,200}[。！？♪♫✨])\1{1,}', r'\1', text)

            # 6. 全局去重 - 更激进
            text = re.sub(r'(.{4,50})\1{2,}', r'\1', text)

            # 7. 去除连续重复的两行
            lines = text.split('\n')
            if len(lines) >= 4:
                new_lines = []
                for i in range(len(lines) - 1):
                    # 如果连续3行相同，跳过中间的行
                    if i + 2 < len(lines) and lines[i].strip() == lines[i+1].strip() == lines[i+2].strip():
                        continue
                    new_lines.append(lines[i])
                new_lines.append(lines[-1])
                text = '\n'.join(new_lines)

            # 8. 去除句尾重复的短语（如 "的呢~的呢~"）
            text = re.sub(r'(.{1,10})\1{2,}$', r'\1', text)
            text = re.sub(r'(.{1,10})\1{2,}', r'\1', text)

            # 9. 去除连续重复的句子片段（不同长度）
            for min_len in [5, 8, 12, 15, 20]:
                for max_len in [15, 20, 30, 40, 50]:
                    if min_len < max_len:
                        text = re.sub(r'(.{%d,%d})\1{1,}' % (min_len, max_len), r'\1', text)

            # 10. 去除emoji和符号的连续重复
            text = re.sub(r'([♪♫✨💕❤️🌸🎵])\1{2,}', r'\1', text)
            text = re.sub(r'([。！？~])\1{3,}', r'\1\1', text)

            # 11. 去除相同开头的连续句子
            sentences = re.split(r'([。！？])', text)
            if len(sentences) > 3:
                new_sentences = []
                for i in range(0, len(sentences)-1, 2):
                    if i == 0:
                        new_sentences.append(sentences[i])
                    else:
                        # 检查当前句是否与前一句相同
                        curr = sentences[i] + sentences[i+1] if i+1 < len(sentences) else sentences[i]
                        prev = new_sentences[-1] if new_sentences else ""
                        if curr.strip() != prev.strip():
                            new_sentences.append(curr)
                text = ''.join(new_sentences)

            # 12. 最终全局去重扫描
            text = re.sub(r'(.{3,30})\1{3,}', r'\1', text)

            # 检查是否有变化
            if text == prev_text:
                break
            original = text

        return text.strip()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        learned_context: str = "",
    ) -> str:
        """单轮对话"""
        client = self._get_client()

        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        full_system = system_prompt
        if learned_context:
            full_system += f"\n\n【已学习的知识】:\n{learned_context}"

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=full_system if full_system else "You are a helpful assistant.",
            messages=anthropic_messages,
            temperature=temperature
        )

        return self._extract_text(response)

    async def chat_full(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        learned_context: str = "",
    ) -> str:
        """获取完整响应（非流式）"""
        client = self._get_client()

        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        full_system = system_prompt
        if learned_context:
            full_system += f"\n\n【已学习的知识】:\n{learned_context}"

        full_system += "\n\n【重要】: 请尽量不要重复之前说过的话，保持回复的多样性和新颖性。"

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=full_system if full_system else "You are a helpful assistant.",
                messages=anthropic_messages,
                temperature=temperature
            )
            return self._extract_text(response)
        except Exception as e:
            print(f"[ERROR] LLM error: {e}")
            return "抱歉，我遇到了一些问题。"

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        learned_context: str = "",
        use_stream_dedup: bool = True,
    ) -> AsyncGenerator[str, None]:
        """流式对话（先获取完整响应，再模拟流式输出）"""
        print(f"\n[STEP 1] 开始调用 LLM...")

        # 先获取完整响应
        full_response = await self.chat_full(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            learned_context=learned_context,
        )

        print(f"[STEP 2] LLM 响应完成，长度: {len(full_response)} 字符")

        # 保存原始输出
        original_response = full_response
        print(f"\n========== AI 原始输出 ==========\n{original_response}\n===================================\n")

        print(f"[STEP 3] 开始去重处理...")

        # 强力去重（后处理）
        full_response = self._deduplicate_text(full_response)

        # 打印去重后的输出
        print(f"\n========== 去重后输出 ==========\n{full_response}\n===================================\n")
        print(f"[STEP 4] 去重完成，长度: {len(full_response)} 字符")

        # 创建流式去重器
        dedup = BufferedDeduplicator(
            buffer_size=100,
            flush_interval=0.05,
            n=4
        ) if use_stream_dedup else None

        print(f"[STEP 5] 开始模拟流式输出...")

        # 模拟流式输出：每次发送更多字符，减少延迟
        chunk_size = 15  # 每次发送15个字符
        delay = 0.01     # 延迟0.01秒

        for i in range(0, len(full_response), chunk_size):
            text_chunk = full_response[i:i + chunk_size]

            if dedup:
                # 使用流式去重器处理每个 chunk
                deduped = await dedup.process_chunk(text_chunk)
                if deduped:
                    yield deduped
            else:
                yield text_chunk

            await asyncio.sleep(delay)

        # 刷新剩余内容
        if dedup:
            remaining = await dedup.flush_remaining()
            if remaining:
                yield remaining

        print(f"[STEP 6] 流式输出完成")

    async def chat_with_docs(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        docs_context: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        learned_context: str = "",
    ) -> str:
        """带文档上下文的对话"""
        client = self._get_client()

        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        full_system = system_prompt

        if docs_context:
            full_system += f"\n\n【参考文档内容】:\n{docs_context}"

        if learned_context:
            full_system += f"\n\n【已学习的知识】:\n{learned_context}"

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=full_system if full_system else "You are a helpful assistant.",
            messages=anthropic_messages,
            temperature=temperature
        )

        return self._extract_text(response)

    def _extract_text(self, response) -> str:
        """从响应中提取文本"""
        text_parts = []
        for block in response.content:
            if hasattr(block, 'text'):
                text_parts.append(block.text)
            elif isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
        return "\n".join(text_parts)


# 全局实例
llm_service = LLMService()
