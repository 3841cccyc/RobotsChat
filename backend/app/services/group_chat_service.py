from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.services.streaming_dedup import BufferedDeduplicator, HistoryChecker
from app.models import Bot, GroupConversation, GroupMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional, AsyncGenerator
import asyncio
import re
import uuid


class GroupChatService:
    """群聊服务 - 多机器人自动聊天"""
    
    def __init__(self):
        self.turn_delay = 1.0  # 轮次之间延迟
        self._active_loops: Dict[int, str] = {}  # 并发控制：{conversation_id: loop_id}
    
    def _acquire_lock(self, conversation_id: int) -> str:
        """获取会话锁，防止并发"""
        # 如果已经有活跃的循环，返回 None（锁被占用）
        if conversation_id in self._active_loops:
            return None
        
        # 创建新锁
        loop_id = str(uuid.uuid4())
        self._active_loops[conversation_id] = loop_id
        return loop_id
    
    def _release_lock(self, conversation_id: int, loop_id: str):
        """释放会话锁"""
        if self._active_loops.get(conversation_id) == loop_id:
            del self._active_loops[conversation_id]

    def _parse_mentions(self, text: str, bots: List[Bot]) -> List[Bot]:
        """
        解析用户消息中的@mentions，返回被@的机器人列表

        支持:
        - @机器人名 (模糊匹配，不区分大小写)
        - @all / @ALL (所有机器人响应)
        - @所有人 (所有机器人响应)

        Args:
            text: 用户消息内容
            bots: 可用机器人列表

        Returns:
            被@的机器人列表，如果无@则返回空列表
        """
        if not text or not bots:
            return []

        mentioned_bots = []
        text_lower = text.lower()

        # 检查@all或@所有人
        if '@all' in text_lower or '@所有人' in text_lower:
            return bots  # 返回所有机器人

        # 匹配@后跟机器人名 (模糊匹配)
        # 正则: @(\w+) 匹配@后跟字母数字下划线
        mention_pattern = re.compile(r'@(\w+)', re.IGNORECASE)
        mentions = mention_pattern.findall(text)

        for mention in mentions:
            mention_lower = mention.lower()

            # 查找匹配的机器人（模糊匹配，名称包含mention或mention包含名称）
            for bot in bots:
                bot_name_lower = bot.name.lower()
                if (mention_lower in bot_name_lower or
                    bot_name_lower in mention_lower or
                    mention_lower == bot_name_lower):
                    if bot not in mentioned_bots:
                        mentioned_bots.append(bot)

        return mentioned_bots

    def _select_next_bot(
        self,
        bots: List[Bot],
        activation_strategy: int,
        last_bot: Bot = None,
        last_message: str = ""
    ) -> List[Bot]:
        """
        根据激活策略选择下一个发言的机器人

        Args:
            bots: 可用的机器人列表
            activation_strategy: 激活策略 (0-自然顺序, 1-列表顺序, 2-池化激活, 3-手动激活, 4-随机激活, 5-相关激活)
            last_bot: 上一个发言的机器人
            last_message: 上一条消息内容

        Returns:
            排序后的机器人列表
        """
        import random

        if not bots:
            return bots

        # 策略0-1: 自然顺序或列表顺序 - 保持原顺序
        if activation_strategy in [0, 1]:
            return bots

        # 策略4: 随机激活 - 随机打乱顺序
        if activation_strategy == 4:
            shuffled = bots.copy()
            random.shuffle(shuffled)
            return shuffled

        # 策略5: 相关激活 - 基于消息关键词选择相关机器人
        if activation_strategy == 5 and last_message:
            # 简单关键词匹配：检查机器人名称/描述是否与消息相关
            keywords = last_message.lower().split()
            scored_bots = []

            for bot in bots:
                score = 0
                bot_text = f"{bot.name} {bot.system_prompt}".lower()

                # 检查关键词匹配
                for kw in keywords:
                    if len(kw) > 2 and kw in bot_text:
                        score += 1

                # 如果是第一个发言，给一定基础分
                if last_bot is None:
                    score += 0.5

                scored_bots.append((score, bot))

            # 按分数降序排序
            scored_bots.sort(key=lambda x: x[0], reverse=True)
            return [bot for _, bot in scored_bots]

        # 默认：返回原顺序
        return bots

    def _build_context_for_bot(self, bot: Bot, all_messages: List[Dict], include_docs: bool = False) -> tuple:
        """
        为特定机器人构建上下文
        - 人格隔离：只传递群聊消息历史，不传递其他机器人的 system prompt
        """
        # 构建群聊历史（所有人都能看到）
        group_history = []
        for msg in all_messages:
            if msg.get("sender_name"):
                group_history.append({
                    "role": msg["role"],
                    "content": f"{msg['sender_name']}: {msg['content']}"
                })
        
        # 构建系统提示词（只有自己的）
        system_prompt = bot.system_prompt
        system_prompt += "\n\n你正在参与一个多人群聊。请根据对话历史，用你的角色风格回复。"
        
        # 添加文档上下文
        if include_docs and all_messages:
            # 使用最后一条用户消息进行检索
            last_user_msg = ""
            for msg in reversed(all_messages):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break
            if last_user_msg:
                # 异步获取文档（这里简化处理）
                pass
        
        return system_prompt, group_history
    
    async def _generate_bot_response_stream(
        self,
        bot: Bot,
        messages: List[Dict],
        all_messages: List[Dict],
    ) -> AsyncGenerator[str, None]:
        """流式生成机器人回复"""

        # 构建系统提示词（只有自己的 system prompt）
        system_prompt = bot.system_prompt
        system_prompt += "\n\n你正在参与一个多人群聊。请根据对话历史，用你的角色风格回复。"

        # 添加防重复指令
        system_prompt += "\n\n【重要规则】:\n"
        system_prompt += "1. 不要重复自己或他人已经说过的话\n"
        system_prompt += "2. 保持回复简洁有力，不要冗余\n"
        system_prompt += "3. 用独特的表达方式回应\n"

        # 添加其他人的发言作为上下文（但不是他们的 system prompt）
        if all_messages:
            other_messages = []
            for msg in all_messages:
                if msg.get("sender_name") and msg.get("sender_name") != bot.name:
                    other_messages.append(
                        f"{msg['sender_name']}: {msg['content']}"
                    )
            if other_messages:
                system_prompt += f"\n\n【群聊历史】:\n" + "\n".join(other_messages)

        # 创建历史消息检查器
        history_checker = HistoryChecker(max_history=10)

        # 添加之前机器人的回复到历史
        for msg in all_messages:
            if msg.get("sender_name") == bot.name:
                history_checker.add_message(msg.get("content", ""))

        # 创建带历史检查的缓冲区去重器
        dedup = BufferedDeduplicator(
            buffer_size=100,
            flush_interval=0.05,
            n=4
        )
        dedup.set_history_checker(history_checker)

        # 流式生成回复，使用流式去重
        full_response = ""
        async for text_chunk in llm_service.chat_stream(
            messages=messages,
            system_prompt=system_prompt,
            temperature=bot.temperature,
            max_tokens=bot.max_tokens,
            use_stream_dedup=True
        ):
            # 额外的内联去重：移除末尾重复片段
            cleaned = dedup.ngram_detector.get_unique_tail(text_chunk)
            if cleaned:
                yield cleaned
                full_response += cleaned

        # 流式结束后，将完整回复添加到历史
        if full_response:
            history_checker.add_message(full_response)
    
    def _deduplicate_and_split(self, text: str, previous_content: str = "") -> tuple:
        """
        去除重复内容并拆分成长短合适的消息
        返回: (处理后的文本, 是否应该拆分新消息)
        """
        if not text:
            return text, False
        
        # 1. 去除与之前内容重复的部分
        if previous_content:
            # 检查新文本是否以之前内容开头
            if text.startswith(previous_content):
                text = text[len(previous_content):]
        
        # 2. 去除连续重复的短语（如 "你好呀！你好呀！"）
        # 匹配连续重复2次及以上的词组（3-15个字符）
        pattern = r'(.{3,15})\1{1,}'
        text = re.sub(pattern, r'\1', text)
        
        # 3. 去除句内重复 - 优化版本，使用 Set 避免重复检查
        if len(text) > 20:
            seen_substrings = set()  # 已检查过的子串
            text_parts = []
            last_end = 0

            for i in range(len(text) - 10):
                if i > len(text) - 20:
                    break

                # 滑动窗口：子串长度从 10 到 30
                for length in range(10, min(31, len(text) - i)):
                    substring = text[i:i + length]
                    if substring in seen_substrings:
                        continue
                    seen_substrings.add(substring)

                    remaining = text[i + length:]
                    if substring in remaining:
                        text_parts.append(text[last_end:i])
                        last_end = i + length + remaining.find(substring) + length
                        break

            if text_parts:
                text_parts.append(text[last_end:])
                text = ''.join(text_parts)
        
        # 4. 拆分长消息（每60-100字符为一个短消息）
        # 找到合适的断点（句号、问号、感叹号、逗号+空格等）
        should_split = len(text) > 80
        
        return text.strip(), should_split
    
    def _split_into_short_messages(self, text: str, max_length: int = 20) -> List[str]:
        """
        将长文本拆分成多个短消息，每条最多max_length个字符
        断点优先级：句号/问号/感叹号 > 逗号/顿号 > 强制截断
        """
        if not text or len(text) <= max_length:
            return [text] if text else []

        messages = []
        current = ""

        # 断点优先级：第一优先级-句号/感叹号/问号，第二优先级-逗号/顿号
        primary_breakpoints = ['。', '！', '？']  # 句号、感叹号、问号
        secondary_breakpoints = ['，', '、']      # 逗号、顿号

        for char in text:
            current += char

            # 检查是否到达最大长度
            if len(current) >= max_length:
                # 尝试找到最近的断点
                breakpoint_pos = -1
                breakpoint_type = None

                # 先找主要断点（句号、问号、感叹号）
                for bp in primary_breakpoints:
                    pos = current.rfind(bp)
                    if pos > 0 and pos < len(current):
                        breakpoint_pos = pos + 1  # 包含标点
                        breakpoint_type = 'primary'
                        break

                # 如果没有主要断点，找次要断点
                if breakpoint_pos == -1:
                    for bp in secondary_breakpoints:
                        pos = current.rfind(bp)
                        if pos > 5:  # 至少5个字符
                            breakpoint_pos = pos + 1
                            breakpoint_type = 'secondary'
                            break

                # 如果找到断点且不是太短，在断点处拆分
                if breakpoint_pos > 5:
                    messages.append(current[:breakpoint_pos].strip())
                    current = current[breakpoint_pos:]
                else:
                    # 强制拆分
                    messages.append(current.strip())
                    current = ""

        # 添加剩余内容
        if current.strip():
            messages.append(current.strip())

        return messages
    
    def _deduplicate_response(self, text: str) -> str:
        """去除回复中的重复内容（兼容旧接口）"""
        cleaned, _ = self._deduplicate_and_split(text)
        return cleaned

    def truncate_messages(self, messages: List[Dict], max_tokens: int = 4000, max_count: int = 20) -> List[Dict]:
        """
        根据 token 数量和消息数量限制截断历史消息

        Args:
            messages: 消息列表
            max_tokens: 最大 token 数（默认 4000）
            max_count: 最大消息数量（默认 20）

        Returns:
            截断后的消息列表
        """
        if not messages:
            return []

        # 首先按数量限制
        if len(messages) <= max_count:
            return messages

        # 粗略估算：中文约 1.5 字符/token，英文约 4 字符/token
        # 取平均值约 2 字符/token
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        estimated_tokens = total_chars / 2

        # 如果 token 数在限制内，直接返回
        if estimated_tokens <= max_tokens:
            return messages

        # 否则从最新的消息开始保留，逐一添加直到达到限制
        truncated = []
        current_tokens = 0

        # 从最新的消息开始添加
        for msg in reversed(messages):
            msg_tokens = len(msg.get("content", "")) / 2
            if current_tokens + msg_tokens > max_tokens or len(truncated) >= max_count:
                break
            truncated.insert(0, msg)
            current_tokens += msg_tokens

        return truncated

    async def start_group_chat_stream(
        self,
        db: AsyncSession,
        bot_ids: List[int],
        user_id: Optional[int] = None,
        user_name: str = "用户",
        user_prompt: str = "",
        topic: str = "",
        include_docs: bool = False
    ) -> AsyncGenerator[Dict, None]:
        """
        启动群聊（流式输出）
        用户发第一条消息，所有机器人依次回复
        """
        # 获取所有机器人
        bots = []
        for bot_id in bot_ids:
            result = await db.execute(select(Bot).where(Bot.id == bot_id))
            bot = result.scalar_one_or_none()
            if bot:
                bots.append(bot)
        
        if not bots:
            raise ValueError("没有找到有效的机器人")
        
        # 创建群聊会话
        conversation = GroupConversation(
            title=topic or "群聊",
            bot_id=bots[0].id
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        messages = []
        
        # 如果有用户消息，保存并添加到历史
        if user_prompt:
            user_message = GroupMessage(
                conversation_id=conversation.id,
                role="user",
                content=user_prompt,
                sender_name=user_name
            )
            db.add(user_message)
            await db.commit()
            messages.append({
                "role": "user",
                "content": user_prompt,
                "sender_name": user_name
            })
        
        # 按顺序让每个机器人发言
        for bot in bots:
            # 获取该机器人的消息上下文
            bot_messages = self._get_bot_context(messages, bot.name)
            
            # 流式生成回复
            full_response = ""
            async for text_chunk in self._generate_bot_response_stream(
                bot=bot,
                messages=bot_messages,
                all_messages=messages
            ):
                full_response += text_chunk
                # 发送流式片段
                yield {
                    "type": "chunk",
                    "bot_name": bot.name,
                    "bot_id": bot.id,
                    "content": text_chunk,
                    "conversation_id": conversation.id
                }
            
            # 应用去重
            full_response = self._deduplicate_response(full_response)
            
            # 保存完整消息
            if full_response:
                bot_message = GroupMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                    sender_name=bot.name
                )
                db.add(bot_message)
                await db.commit()
                
                messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sender_name": bot.name,
                    "bot_id": bot.id
                })
            
            # 延迟
            await asyncio.sleep(self.turn_delay)
        
        # 发送完成信号
        yield {
            "type": "done",
            "conversation_id": conversation.id,
            "messages": messages
        }
    
    def _get_bot_context(self, all_messages: List[Dict], bot_name: str) -> List[Dict]:
        """获取特定机器人的对话上下文"""
        bot_messages = []
        
        for msg in all_messages:
            if msg.get("sender_name") == bot_name:
                # 自己的历史消息
                bot_messages.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "user":
                # 用户的消息
                bot_messages.append({"role": "user", "content": msg["content"]})
            elif msg.get("sender_name"):
                # 其他人的消息也添加（但作为用户消息类型，让机器人知道是谁说的）
                bot_messages.append({
                    "role": "user", 
                    "content": f"【{msg['sender_name']}说】: {msg['content']}"
                })
        
        # 如果没有历史消息，返回用户消息作为上下文
        if not bot_messages:
            for msg in all_messages:
                if msg["role"] == "user":
                    bot_messages.append({"role": "user", "content": msg["content"]})
                    break
        
        return bot_messages
    
    async def add_user_message_stream(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_name: str,
        user_prompt: str,
        bots: List[Bot],
        include_docs: bool = False
    ) -> AsyncGenerator[Dict, None]:
        """
        在群聊中添加用户消息，机器人依次回复（流式输出）
        """
        
        # 获取会话中的历史消息
        result = await db.execute(
            select(GroupMessage).where(GroupMessage.conversation_id == conversation_id)
        )
        history_messages = result.scalars().all()
        
        # 转换为消息格式
        all_messages = []
        for msg in history_messages:
            all_messages.append({
                "role": msg.role,
                "content": msg.content,
                "sender_name": msg.sender_name or ""
            })
        
        # 添加当前用户消息
        all_messages.append({
            "role": "user",
            "content": user_prompt,
            "sender_name": user_name
        })
        
        # 保存用户消息
        user_message = GroupMessage(
            conversation_id=conversation_id,
            role="user",
            content=user_prompt,
            sender_name=user_name
        )
        db.add(user_message)
        await db.commit()

        # 发送用户消息确认
        yield {
            "type": "user_message",
            "content": user_prompt,
            "sender_name": user_name
        }

        # 解析@mentions
        mentioned_bots = self._parse_mentions(user_prompt, bots)

        # 发送mentions解析结果
        yield {
            "type": "mentions_parsed",
            "mentioned_bot_names": [b.name for b in mentioned_bots],
            "total_bots": len(bots)
        }

        # 确定响应的机器人列表
        if mentioned_bots:
            responding_bots = mentioned_bots  # 只让被@的机器人响应
        else:
            responding_bots = bots  # 没有@时所有机器人响应

        # 让筛选后的机器人依次回复
        for bot in responding_bots:
            # 获取该机器人的上下文
            bot_messages = self._get_bot_context(all_messages, bot.name)
            
            # 流式生成回复
            full_response = ""
            async for text_chunk in self._generate_bot_response_stream(
                bot=bot,
                messages=bot_messages,
                all_messages=all_messages
            ):
                full_response += text_chunk
                # 发送流式片段
                yield {
                    "type": "chunk",
                    "bot_name": bot.name,
                    "bot_id": bot.id,
                    "content": text_chunk,
                    "conversation_id": conversation_id
                }
            
            # 应用去重
            full_response = self._deduplicate_response(full_response)
            
            # 保存回复
            if full_response:
                bot_message = GroupMessage(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                    sender_name=bot.name
                )
                db.add(bot_message)
                await db.commit()
                
                # 更新消息列表
                all_messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sender_name": bot.name,
                    "bot_id": bot.id
                })
            
            # 延迟
            await asyncio.sleep(self.turn_delay)
        
        # 发送完成信号
        yield {
            "type": "done",
            "conversation_id": conversation_id
        }


# 全局实例
group_chat_service = GroupChatService()


# ==================== 自动聊天扩展方法 ====================

async def auto_chat_rounds(
    service: GroupChatService,
    db: AsyncSession,
    conversation_id: int,
    bots: List[Bot],
    all_messages: List[Dict],
    auto_rounds: int = 3,
    loop_id: str = None
) -> AsyncGenerator[Dict, None]:
    """
    自动聊天多轮回复
    
    Args:
        service: GroupChatService 实例
        db: 数据库会话
        conversation_id: 会话ID
        bots: 机器人列表
        all_messages: 已有消息历史
        auto_rounds: 自动回复轮数（3-5）
        loop_id: 循环ID（用于并发控制）
    """
    current_round = 0
    
    while current_round < auto_rounds:
        # 检查是否还有轮次
        remaining = auto_rounds - current_round
        is_final_round = remaining == 1
        
        for bot in bots:
            # 检查是否应该停止
            if loop_id and service._active_loops.get(conversation_id) != loop_id:
                # 锁被释放，停止自动聊天
                yield {
                    "type": "auto_stopped",
                    "reason": "user_stopped",
                    "conversation_id": conversation_id
                }
                return
            
            # 获取该机器人的上下文
            bot_messages = service._get_bot_context(all_messages, bot.name)
            
            # 添加系统提示（包含是否是最后一轮）
            system_prompt = bot.system_prompt
            system_prompt += "\n\n你正在参与一个多人群聊。"
            
            if is_final_round:
                # 最后一轮，添加"钩子"提示
                system_prompt += "\n\n【重要】这是最后一轮对话了，请在回复结束时添加一些互动性的问题或提议，比如："
                system_prompt += "\n- '哎呀，我是不是说得太多啦？'"
                system_prompt += "\n- '好了，我先休息一下，你们继续聊~'"
                system_prompt += "\n- '大家还有什么想聊的吗？'"
                system_prompt += "\n让对话自然地结束，给用户继续的机会。"
            else:
                system_prompt += "\n\n请根据对话历史，用你的角色风格回复。"
            
            # 添加历史上下文（使用向量检索）
            context = await rag_service.search_group_history(
                conversation_id=conversation_id,
                query=all_messages[-1].get("content", "") if all_messages else "",
                recent_messages=all_messages[-10:] if all_messages else [],
                k=3
            )
            if context:
                system_prompt += f"\n\n【相关对话上下文】:\n{context}"
            
            # 发送机器人开始信号
            yield {
                "type": "bot_start",
                "bot_name": bot.name,
                "bot_id": bot.id,
                "round": current_round + 1,
                "total_rounds": auto_rounds,
                "is_final": is_final_round
            }
            
            # 流式生成回复（llm_service.chat_stream 已经做了去重）
            full_response = ""
            print(f"[AUTO_CHAT] 机器人 {bot.name} 开始生成...")
            chunk_count = 0
            async for text_chunk in llm_service.chat_stream(
                messages=bot_messages,
                system_prompt=system_prompt,
                temperature=bot.temperature,
                max_tokens=bot.max_tokens
            ):
                chunk_count += 1
                if chunk_count <= 3:
                    print(f"[AUTO_CHAT] 收到 chunk {chunk_count}: {repr(text_chunk[:30])}...")

                full_response += text_chunk
                yield {
                    "type": "chunk",
                    "bot_name": bot.name,
                    "bot_id": bot.id,
                    "content": text_chunk,
                    "conversation_id": conversation_id
                }

            print(f"[AUTO_CHAT] 机器人 {bot.name} 完成，共 {chunk_count} 个 chunk")
            
            # 应用去重
            full_response = service._deduplicate_response(full_response)
            
            # 拆分消息为多条短消息
            short_messages = service._split_into_short_messages(full_response, max_length=20)
            
            # 如果需要拆分，逐条发送
            if len(short_messages) > 1:
                # 先发送 bot_done 信号表示第一段完成
                yield {
                    "type": "message_split",
                    "bot_name": bot.name,
                    "total_parts": len(short_messages),
                    "conversation_id": conversation_id
                }
                
                # 逐条发送拆分后的消息，每条之间有延迟
                for i, msg in enumerate(short_messages[1:], 1):
                    # 检查是否应该停止
                    if loop_id and service._active_loops.get(conversation_id) != loop_id:
                        return
                    
                    yield {
                        "type": "chunk",
                        "bot_name": bot.name,
                        "bot_id": bot.id,
                        "content": msg,
                        "conversation_id": conversation_id,
                        "part": i + 1,
                        "total_parts": len(short_messages)
                    }
                    
                    # 1秒固定间隔
                    await asyncio.sleep(1.0)
            
            # 保存回复到数据库
            if full_response:
                bot_message = GroupMessage(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                    sender_name=bot.name
                )
                db.add(bot_message)
                await db.commit()
                
                # 同时保存到向量库
                await rag_service.add_group_message(
                    conversation_id=conversation_id,
                    message=full_response,
                    sender_name=bot.name
                )
                
                # 更新消息列表
                all_messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sender_name": bot.name,
                    "bot_id": bot.id
                })
            
            # 发送机器人完成信号
            yield {
                "type": "bot_done",
                "bot_name": bot.name,
                "round": current_round + 1
            }
            
            # 计算动态延迟（模拟人类打字时间）
            delay = rag_service.calculate_typing_delay(full_response) if full_response else 1.0
            await asyncio.sleep(delay)
        
        current_round += 1
    
    # 发送自动聊天完成信号
    yield {
        "type": "auto_complete",
        "conversation_id": conversation_id,
        "rounds_completed": current_round,
        "message": "机器人自动聊天已完成，等待用户确认是否继续"
    }
