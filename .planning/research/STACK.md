# Technology Stack: Streaming Output Deduplication

**Project:** 机器人对话系统 (Chatbot System)
**Researched:** 2026-03-14
**Focus:** 流式输出去重、异步处理、消息截断

## Executive Summary

本项目已采用 FastAPI + MiniMax LLM + SQLAlchemy 异步架构。当前实现是"先获取完整响应再模拟流式输出"的方式，去重逻辑在流式输出前执行。要实现真正的实时流式去重，需要以下技术栈升级。

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | >=0.100 | 异步 Web 框架 | 原生支持异步流式响应 (StreamingResponse)，与本项目当前架构一致 |
| Python | 3.10+ | 运行时 | 支持 asyncio.streamiterator 等高级异步特性 |

### Streaming Deduplication

| Technology | Purpose | Why |
|------------|---------|-----|
| 自研滑动窗口去重器 | 实时流式去重 | LLM 流式输出的重复检测需要按字符/词组滑动窗口检测，无法简单套用现有库 |
| difflib.SequenceMatcher | 相似度检测 | Python 标准库，适合检测近似重复片段 |
| re (正则表达式) | 模式匹配去重 | 项目已有实现，可复用 `_deduplicate_text` 逻辑 |

### Async Streaming Processing

| Technology | Purpose | Why |
|------------|---------|-----|
| asyncio.StreamReader | 异步流读取 | Python 标准库，处理异步字节流 |
| async generator | 流式生成器 | FastAPI 原生支持 `AsyncGenerator` 作为流式响应 |
| contextlib.asynccontextmanager | 资源管理 | 项目已在 `main.py` 使用，可扩展到流式处理 |

### Message Truncation

| Technology | Purpose | Why |
|------------|---------|-----|
| textwrap 模块 | 文本包装 | Python 标准库，支持按宽度截断 |
| nltk/tokenize | 智能分句 | 保持句子完整性，适合长文本拆分 |
| 自研消息分块器 | 按消息数量拆分 | 针对聊天场景优化，控制单条消息长度 |

## Alternative Approaches

### Approach 1: 后处理去重 (当前实现)

```
LLM → 完整响应 → 去重 → 模拟流式输出
```

**优点:** 实现简单，去重彻底
**缺点:** 用户需要等待 LLM 完整响应才能开始接收输出

### Approach 2: 实时流式去重 (推荐)

```
LLM 流式输出 → 滑动窗口检测 → 实时过滤 → 前端推送
```

**优点:** 用户更快看到首个 token，减少等待时间
**缺点:** 实现复杂，需要维护状态

### Approach 3: 混合策略 (最佳实践)

```
LLM 流式输出 → 缓冲区 → 批量去重 → 定时推送
```

**优点:** 平衡实时性和去重效果
**实现:** 使用缓冲区收集一定量内容后批量去重，再推送到前端

## Implementation Patterns

### Pattern 1: 滑动窗口去重器

```python
import asyncio
from typing import AsyncGenerator

class StreamingDeduplicator:
    """流式输出去重器"""

    def __init__(self, window_size: int = 50, min_duplicate_len: int = 5):
        self.window_size = window_size
        self.min_duplicate_len = min_duplicate_len
        self.buffer = ""
        self.seen_patterns = set()

    async def process_chunk(self, chunk: str) -> str:
        """处理单个 chunk，返回去重后的内容"""
        self.buffer += chunk

        # 只在缓冲区足够大时检查
        if len(self.buffer) < self.min_duplicate_len:
            return chunk

        # 检查尾部是否包含重复模式
        result = self._check_and_remove_duplicate(self.buffer)
        return result

    def _check_and_remove_duplicate(self, text: str) -> str:
        """检查并移除重复"""
        # 使用滑动窗口检测末尾重复
        for pattern_len in range(self.min_duplicate_len, self.window_size):
            if len(text) < pattern_len * 2:
                continue

            # 检查最后两个片段是否相同
            suffix = text[-pattern_len:]
            if text[-pattern_len*2:-pattern_len] == suffix:
                # 移除重复部分
                return text[:-pattern_len]

        return text
```

### Pattern 2: 异步流式响应封装

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
import json

async def streaming_deduplication_response(llm_generator: AsyncGenerator[str, None]):
    """带去重的流式响应"""
    deduplicator = StreamingDeduplicator(window_size=30, min_duplicate_len=3)

    async for chunk in llm_generator:
        # 实时去重
        deduped_chunk = await deduplicator.process_chunk(chunk)
        if deduped_chunk:
            # SSE 格式
            yield f"data: {json.dumps({'content': deduped_chunk})}\n\n"
            await asyncio.sleep(0)  # 让出控制权

    yield "data: [DONE]\n\n"
```

### Pattern 3: 消息截断算法

```python
import re
from typing import List

class MessageTruncator:
    """长消息截断器 - 保持句子完整性"""

    # 句子结束标记
    SENTENCE_ENDINGS = re.compile(r'[。！？!?.\n]+')

    def __init__(self, max_chars: int = 500, overlap: int = 20):
        self.max_chars = max_chars
        self.overlap = overlap  # 重叠字符数，避免句子被切断

    def split(self, text: str) -> List[str]:
        """将长文本拆分为短消息列表"""
        if len(text) <= self.max_chars:
            return [text]

        messages = []
        start = 0

        while start < len(text):
            end = start + self.max_chars

            # 尽量在句子边界处截断
            if end < len(text):
                # 查找最近的句子结束标记
                match = self.SENTENCE_ENDINGS.search(text[end:end+50])
                if match:
                    end += match.end()

            # 添加重叠区域，避免句子被切断
            chunk = text[start:end]
            messages.append(chunk)

            start = end - self.overlap if end < len(text) else end

        return messages

    def split_by_count(self, text: str, max_messages: int = 10) -> List[str]:
        """按消息数量拆分"""
        if len(text) <= self.max_chars:
            return [text]

        # 计算每条消息的最大长度
        chars_per_message = max(self.max_chars, len(text) // max_messages)
        return self._split_fixed_width(text, chars_per_message)

    def _split_fixed_width(self, text: str, width: int) -> List[str]:
        """固定宽度拆分，保持单词完整性"""
        words = text.split()
        messages = []
        current = []

        for word in words:
            test = ' '.join(current) + ' ' + word
            if len(test) > width and current:
                messages.append(' '.join(current))
                current = [word]
            else:
                current.append(word)

        if current:
            messages.append(' '.join(current))

        return messages
```

### Pattern 4: 缓冲区批量去重 (推荐)

```python
class BufferedDeduplicator:
    """带缓冲区的去重器 - 平衡实时性和效果"""

    def __init__(
        self,
        buffer_size: int = 100,      # 缓冲区大小
        flush_interval: float = 0.1,  # 刷新间隔(秒)
        min_duplicate_len: int = 5
    ):
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.min_duplicate_len = min_duplicate_len
        self.buffer = ""
        self.last_flush = None

    async def process(
        self,
        input_generator: AsyncGenerator[str, None],
        output_queue: asyncio.Queue
    ):
        """处理流式输入，输出到队列"""
        async for chunk in input_generator:
            self.buffer += chunk

            # 缓冲区满或达到刷新间隔时输出
            if len(self.buffer) >= self.buffer_size:
                await self._flush(output_queue)

        # 处理剩余内容
        if self.buffer:
            await self._flush(output_queue)

        await output_queue.put(None)  # 结束标记

    async def _flush(self, output_queue: asyncio.Queue):
        """刷新缓冲区，进行去重处理"""
        if not self.buffer:
            return

        # 应用去重逻辑
        deduped = self._deduplicate(self.buffer)
        if deduped:
            await output_queue.put(deduped)

        self.buffer = ""

    def _deduplicate(self, text: str) -> str:
        """简化版去重 - 可复用项目的正则去重逻辑"""
        # 使用项目现有的 _deduplicate_text 方法
        from app.services.llm_service import llm_service
        return llm_service._deduplicate_text(text)
```

## Integration with Current Project

### 升级路线

1. **Phase 1: 保留当前实现**
   - 继续使用 "完整响应 + 后去重 + 模拟流式"
   - 优化 `_deduplicate_text` 正则参数

2. **Phase 2: 添加真实流式支持**
   - 使用 MiniMax 的原生流式 API
   - 实现 `StreamingDeduplicator`
   - 添加 `BufferedDeduplicator`

3. **Phase 3: 消息截断增强**
   - 实现 `MessageTruncator`
   - 处理超长响应拆分

### 代码位置建议

```
backend/app/services/
├── llm_service.py          # 已有，保持不变
├── streaming_dedup.py      # 新增：流式去重器
├── message_truncator.py    # 新增：消息截断器
└── streaming_service.py    # 新增：流式服务封装
```

## Dependencies

```bash
# Core (already in use)
fastapi>=0.100.0
uvicorn>=0.23.0
sqlalchemy>=2.0.0
anthropic>=0.18.0

# Optional enhancements
# nltk>=3.8.0  # 智能分句 (可选)
```

## Sources

- FastAPI Streaming Responses: https://fastapi.tiangolo.com/advanced/streaming-response/
- Python asyncio: https://docs.python.org/3/library/asyncio.html
- difflib documentation: https://docs.python.org/3/library/difflib.html
- 项目现有实现: `backend/app/services/llm_service.py`
