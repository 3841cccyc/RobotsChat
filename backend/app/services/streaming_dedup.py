"""
流式输出去重模块 - 实时检测并过滤重复内容

提供三个核心类：
- NGramDetector: n-gram 重复检测
- BufferedDeduplicator: 缓冲区批量去重
- HistoryChecker: 历史消息去重
"""

from collections import deque
from typing import Optional, Deque
import re


class NGramDetector:
    """n-gram 重复检测器"""

    def __init__(self, n: int = 4, min_duplicate_count: int = 2):
        """
        初始化 n-gram 检测器

        Args:
            n: n-gram 大小（默认4）
            min_duplicate_count: 最小重复次数
        """
        self.n = n
        self.min_duplicate_count = min_duplicate_count

    def extract_ngrams(self, text: str) -> list:
        """
        从文本中提取 n-grams（字符级别，支持中文）

        Args:
            text: 输入文本

        Returns:
            n-gram 列表
        """
        if not text or len(text) < self.n:
            return []

        ngrams = []
        for i in range(len(text) - self.n + 1):
            ngrams.append(text[i:i + self.n])
        return ngrams

    def check_duplicate(self, text: str) -> bool:
        """
        检查文本是否包含连续重复的 n-grams

        Args:
            text: 输入文本

        Returns:
            是否存在重复
        """
        if not text or len(text) < self.n * 2:
            return False

        ngrams = self.extract_ngrams(text)
        if len(ngrams) < self.min_duplicate_count:
            return False

        # 检查连续重复
        for i in range(len(ngrams) - self.min_duplicate_count + 1):
            first_ngram = ngrams[i]
            is_duplicate = True
            for j in range(1, self.min_duplicate_count):
                if ngrams[i + j] != first_ngram:
                    is_duplicate = False
                    break
            if is_duplicate:
                return True

        return False

    def get_unique_tail(self, text: str) -> str:
        """
        移除文本末尾连续重复的片段

        Args:
            text: 输入文本

        Returns:
            去重后的文本
        """
        if not text or len(text) < self.n:
            return text

        # 从末尾向前查找重复模式
        ngrams = self.extract_ngrams(text)
        if len(ngrams) < self.min_duplicate_count:
            return text

        # 检查末尾是否有连续重复
        last_ngram = ngrams[-1]
        repeat_count = 1

        for i in range(len(ngrams) - 2, -1, -1):
            if ngrams[i] == last_ngram:
                repeat_count += 1
            else:
                break

        if repeat_count >= self.min_duplicate_count:
            # 保留第一个重复片段
            unique_end_pos = len(text) - (repeat_count * self.n) + self.n
            return text[:unique_end_pos]

        return text


class BufferedDeduplicator:
    """带缓冲区的流式去重器"""

    def __init__(
        self,
        buffer_size: int = 100,
        flush_interval: float = 0.05,
        n: int = 4,
        min_duplicate_len: int = 8
    ):
        """
        初始化缓冲区去重器

        Args:
            buffer_size: 缓冲区大小
            flush_interval: 刷新间隔（秒）
            n: n-gram 大小
            min_duplicate_len: 最小去重长度
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.ngram_detector = NGramDetector(n=n)
        self.min_duplicate_len = min_duplicate_len

        # 缓冲区
        self._buffer: Deque[str] = deque(maxlen=buffer_size)
        self._history_checker: Optional[HistoryChecker] = None

    def set_history_checker(self, history_checker):
        """设置历史消息检查器"""
        self._history_checker = history_checker

    async def process_chunk(self, chunk: str) -> str:
        """
        处理流式 chunk，返回去重后的内容

        Args:
            chunk: 新的文本片段

        Returns:
            去重后的内容（仅在缓冲区刷新时返回）
        """
        if not chunk:
            return ""

        self._buffer.append(chunk)

        # 当缓冲区满时刷新
        if len(self._buffer) >= self.buffer_size:
            return await self._flush()

        return ""

    async def _flush(self) -> str:
        """刷新缓冲区并进行去重"""
        if not self._buffer:
            return ""

        # 合并缓冲区内容
        text = "".join(self._buffer)
        self._buffer.clear()

        # 应用 n-gram 去重
        text = self._deduplicate(text)

        # 应用历史消息去重
        if self._history_checker:
            text = self._history_checker.filter_duplicate(text)

        return text

    def _deduplicate(self, text: str) -> str:
        """应用 n-gram 去重"""
        if not text:
            return text

        # 移除连续重复的 n-grams
        text = self._remove_consecutive_duplicates(text, self.n)

        return text

    def _remove_consecutive_duplicates(self, text: str, n: int) -> str:
        """
        移除连续重复的 n-grams

        Args:
            text: 输入文本
            n: n-gram 大小

        Returns:
            去重后的文本
        """
        if not text or len(text) < n * 2:
            return text

        # 使用滑动窗口检测连续重复
        result = []
        i = 0

        while i < len(text):
            # 检查从位置 i 开始的重复模式
            found_duplicate = False

            # 尝试不同的重复长度
            for repeat_len in range(n, min(len(text) - i, n * 3)):
                pattern = text[i:i + repeat_len]
                if len(pattern) < self.min_duplicate_len:
                    continue

                # 检查后续是否有连续重复
                remaining = text[i + repeat_len:]
                if pattern in remaining[:repeat_len * 2]:
                    # 发现重复，跳过重复部分
                    result.append(pattern)
                    # 跳过所有连续重复
                    skip_len = repeat_len
                    while text[i + skip_len:i + skip_len + repeat_len] == pattern:
                        skip_len += repeat_len
                    i += skip_len
                    found_duplicate = True
                    break

            if not found_duplicate:
                result.append(text[i])
                i += 1

        return "".join(result)

    async def flush_remaining(self) -> str:
        """刷新剩余内容"""
        return await self._flush()


class HistoryChecker:
    """历史消息去重检查器"""

    def __init__(self, max_history: int = 10):
        """
        初始化历史检查器

        Args:
            max_history: 最大历史消息数量
        """
        self.max_history = max_history
        self._history: Deque[str] = deque(maxlen=max_history)
        self._ngram_sets: Deque[set] = deque(maxlen=max_history)

    def add_message(self, message: str):
        """
        添加已发送的消息到历史

        Args:
            message: 消息内容
        """
        if not message:
            return

        self._history.append(message)

        # 提取并存储 n-grams
        detector = NGramDetector(n=4)
        ngrams = set(detector.extract_ngrams(message))
        self._ngram_sets.append(ngrams)

    def filter_duplicate(self, text: str) -> str:
        """
        过滤与历史消息重复的内容

        Args:
            text: 待检查的文本

        Returns:
            过滤后的文本
        """
        if not text or not self._history:
            return text

        # 简单实现：检查文本开头是否与历史消息开头相同
        for hist_msg in self._history:
            if text.startswith(hist_msg[:20]) and len(hist_msg) > 10:
                # 找到匹配，移除重复部分
                overlap_len = len(hist_msg)
                while text.startswith(hist_msg[:overlap_len]) and overlap_len > 0:
                    overlap_len -= 1
                if overlap_len > 0:
                    text = text[overlap_len:]
                break

        return text

    def has_significant_duplicate(self, text: str, threshold: float = 0.8) -> bool:
        """
        检查文本是否与历史消息有显著重复

        Args:
            text: 待检查的文本
            threshold: 相似度阈值

        Returns:
            是否存在显著重复
        """
        if not text or not self._history:
            return False

        detector = NGramDetector(n=4)
        text_ngrams = set(detector.extract_ngrams(text))

        if not text_ngrams:
            return False

        for hist_ngrams in self._ngram_sets:
            if not hist_ngrams:
                continue

            # 计算 Jaccard 相似度
            intersection = len(text_ngrams & hist_ngrams)
            union = len(text_ngrams | hist_ngrams)

            if union > 0:
                similarity = intersection / union
                if similarity >= threshold:
                    return True

        return False
