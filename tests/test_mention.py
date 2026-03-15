import pytest
import sys
import os

# 添加项目路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from unittest.mock import MagicMock

# 导入待测试的类
from app.services.group_chat_service import GroupChatService


class MockBot:
    """模拟Bot对象"""
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.system_prompt = "You are a helpful assistant."
        self.temperature = 0.7
        self.max_tokens = 1000


class TestParseMentions:
    """测试@mention解析功能"""

    def setup_method(self):
        """每个测试方法前初始化服务"""
        self.service = GroupChatService()

    def test_specific_bot_mention(self):
        """测试@提及特定机器人"""
        bots = [
            MockBot(1, "小爱"),
            MockBot(2, "小度"),
            MockBot(3, "Siri")
        ]
        # 测试 "@小爱 你好"
        result = self.service._parse_mentions("@小爱 你好", bots)
        assert len(result) == 1
        assert result[0].name == "小爱"

    def test_all_mention(self):
        """测试@all和@所有人"""
        bots = [
            MockBot(1, "小爱"),
            MockBot(2, "小度"),
            MockBot(3, "Siri")
        ]
        # 测试 "@all"
        result = self.service._parse_mentions("@all", bots)
        assert len(result) == 3
        assert [b.name for b in result] == ["小爱", "小度", "Siri"]

        # 测试 "@所有人"
        result = self.service._parse_mentions("@所有人", bots)
        assert len(result) == 3

    def test_case_insensitive(self):
        """测试@mention不区分大小写"""
        bots = [
            MockBot(1, "XiaoAi"),
            MockBot(2, "小爱")
        ]
        # 测试 "@XIAOAI"
        result = self.service._parse_mentions("@XIAOAI", bots)
        assert len(result) == 1
        assert result[0].name == "XiaoAi"

        # 测试 "@xiaoai"
        result = self.service._parse_mentions("@xiaoai", bots)
        assert len(result) == 1

        # 测试 "@小爱"
        result = self.service._parse_mentions("@小爱", bots)
        assert len(result) == 1

    def test_user_message_with_mention(self):
        """测试用户消息中包含@mention"""
        bots = [
            MockBot(1, "小爱同学"),
            MockBot(2, "小度助手")
        ]
        # 测试 "@小爱同学 你好呀" - 完整名称匹配
        result = self.service._parse_mentions("@小爱同学 你好呀", bots)
        assert len(result) == 1
        assert result[0].name == "小爱同学"

        # 测试 "@小爱 你好呀" - 模糊匹配
        result = self.service._parse_mentions("@小爱 你好呀", bots)
        assert len(result) == 1
        assert result[0].name == "小爱同学"

    def test_no_mention(self):
        """测试无@mention时返回空列表"""
        bots = [
            MockBot(1, "小爱"),
            MockBot(2, "小度")
        ]
        result = self.service._parse_mentions("你好", bots)
        assert result == []

    def test_empty_text(self):
        """测试空文本"""
        bots = [
            MockBot(1, "小爱"),
        ]
        result = self.service._parse_mentions("", bots)
        assert result == []

        result = self.service._parse_mentions(None, bots)
        assert result == []
