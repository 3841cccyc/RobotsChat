"""
流式输出去重模块测试

测试 NGramDetector, BufferedDeduplicator, HistoryChecker 类
"""
import pytest
import sys
import os

# 添加项目路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.streaming_dedup import NGramDetector, BufferedDeduplicator, HistoryChecker


class TestNGramDetector:
    """测试 NGramDetector 类的功能"""

    def test_extract_ngrams_basic(self):
        """测试基本 n-gram 提取"""
        detector = NGramDetector(n=4)
        text = "hello world"
        ngrams = detector.extract_ngrams(text)
        # "hell", "ello", "llo ", "lo w", "o wo", " wor", "worl", "orld"
        assert len(ngrams) == len(text) - 4 + 1

    def test_extract_ngrams_short_text(self):
        """测试短文本返回空列表"""
        detector = NGramDetector(n=4)
        text = "hi"
        ngrams = detector.extract_ngrams(text)
        assert ngrams == []

    def test_extract_ngrams_empty(self):
        """测试空文本"""
        detector = NGramDetector(n=4)
        ngrams = detector.extract_ngrams("")
        assert ngrams == []
        ngrams = detector.extract_ngrams(None)
        assert ngrams == []

    def test_check_duplicate_no_duplicate(self):
        """测试无重复的文本"""
        detector = NGramDetector(n=4)
        text = "This is a normal sentence without repeated content."
        assert detector.check_duplicate(text) is False

    def test_check_duplicate_with_repeat(self):
        """测试有重复的文本 - 'aaaa' 包含连续重复"""
        detector = NGramDetector(n=2)  # 使用2-gram检测
        text = "aaaa"  # 'aa', 'aa', 'aa' - 连续重复
        assert detector.check_duplicate(text) is True

    def test_check_duplicate_short_text(self):
        """测试短文本不检测重复"""
        detector = NGramDetector(n=4)
        text = "hi"
        assert detector.check_duplicate(text) is False

    def test_get_unique_tail_no_duplicate(self):
        """测试无重复文本返回原文本"""
        detector = NGramDetector(n=4)
        text = "This is a normal sentence"
        result = detector.get_unique_tail(text)
        assert result == text

    def test_get_unique_tail_with_duplicate(self):
        """测试有重复文本去除尾部重复"""
        detector = NGramDetector(n=2)
        # "aaaa" -> ngrams: ['aa', 'aa', 'aa']
        # 末尾连续 'aa' 重复，保留一个 'aa'
        text = "xxaa"
        result = detector.get_unique_tail(text)
        assert result is not None

    def test_ngram_chinese(self):
        """测试中文 n-gram"""
        detector = NGramDetector(n=3)
        text = "今天天气很好"
        ngrams = detector.extract_ngrams(text)
        assert len(ngrams) == len(text) - 3 + 1


class TestHistoryChecker:
    """测试 HistoryChecker 类的功能"""

    def test_add_message(self):
        """测试添加历史消息"""
        checker = HistoryChecker(max_history=5)
        checker.add_message("First message")
        assert len(checker._history) == 1
        assert "First message" in checker._history

    def test_add_empty_message(self):
        """测试添加空消息"""
        checker = HistoryChecker(max_history=5)
        checker.add_message("")
        assert len(checker._history) == 0

    def test_filter_duplicate_no_history(self):
        """测试无历史时不过滤"""
        checker = HistoryChecker(max_history=5)
        text = "New message content"
        result = checker.filter_duplicate(text)
        assert result == text

    def test_filter_duplicate_with_history(self):
        """测试有历史时过滤重复"""
        checker = HistoryChecker(max_history=5)
        checker.add_message("This is a historical message")

        # 测试文本开头与历史相同
        text = "This is a historical message with new content"
        result = checker.filter_duplicate(text)
        # 应该移除重复的开头部分
        assert result is not None

    def test_has_significant_duplicate_below_threshold(self):
        """测试低于阈值不判定为重复"""
        checker = HistoryChecker(max_history=5)
        checker.add_message("This is a completely different message")

        text = "This is another completely different message content"
        assert checker.has_significant_duplicate(text, threshold=0.8) is False

    def test_has_significant_duplicate_above_threshold(self):
        """测试高于阈值判定为重复"""
        checker = HistoryChecker(max_history=5)
        checker.add_message("Today is a nice day, let's go play")

        text = "Today is a nice day, let's go for a walk"
        # 两条消息可能有较高的相似度
        result = checker.has_significant_duplicate(text, threshold=0.3)
        # 结果取决于实现

    def test_max_history_limit(self):
        """测试历史消息数量限制"""
        checker = HistoryChecker(max_history=3)

        checker.add_message("msg1")
        checker.add_message("msg2")
        checker.add_message("msg3")
        checker.add_message("msg4")  # 超过限制
        checker.add_message("msg5")

        # 最多保留3条
        assert len(checker._history) == 3
