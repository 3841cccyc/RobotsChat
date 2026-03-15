---
phase: "02-short-message"
plan: "01"
type: "execute"
wave: 2
depends_on: ["01"]
files_modified:
  - "backend/app/services/group_chat_service.py"
  - "backend/app/routers/group_chat.py"
autonomous: true
requirements:
  - "SHORT-01"
  - "SHORT-02"
  - "SHORT-03"
user_setup: []
must_haves:
  truths:
    - "用户看到机器人输出时，每条消息≤20个汉字"
    - "消息拆分点在句号、逗号、问号等自然断点"
    - "多条短消息依次发送，间隔1秒"
    - "用户在群聊中看到连续对话效果"
  artifacts:
    - path: "backend/app/services/group_chat_service.py"
      provides: "_split_into_short_messages 方法，max_length=20"
      contains: "def _split_into_short_messages"
    - path: "backend/app/routers/group_chat.py"
      provides: "event_generator 函数中的短消息延迟发送"
      contains: "async def event_generator"
  key_links:
    - from: "group_chat_service.py._split_into_short_messages"
      to: "router event_generator"
      via: "返回 List[str]"
      pattern: "短消息列表"
---

<objective>
实现20字短消息拆分与连续输出效果

Purpose: 将机器人长输出拆分为≤20字/条的短消息，在自然断点拆分，并间隔1秒依次发送

Output:
- 修改后的 `_split_into_short_messages` 方法（max_length=20）
- 添加延迟机制的 event_generator
</objective>

<execution_context>
@D:/0正事/学习资料/testforcc/.claude/get-shit-done/workflows/execute-plan.md
@D:/0正事/学习资料/testforcc/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@D:/0正事/学习资料/testforcc/backend/app/services/group_chat_service.py
@D:/0正事/学习资料/testforcc/backend/app/routers/group_chat.py

## Key Implementation Details

### From group_chat_service.py (lines 246-280):
Current `_split_into_short_messages`:
- max_length=80 (需要改为 20)
- breakpoints = ['。', '！', '？', '；', '，', '.', '!', '?', ';', ',']
- splits when breakpoint found AND len(current) >= 30 (需要调整为更短的阈值)

### From group_chat.py (lines 138-251):
Current event_generator:
- After receiving full_response, calls `_deduplicate_and_split` and `_split_into_short_messages`
- But doesn't send short messages with delay - just sends a split signal

### User Requirements (from CONTEXT.md):
- 截断时机: 事后拆分
- 断点优先级: 句号(。)、问号(？)、感叹号(！) > 逗号(，) > 强制截断
- 发送间隔: 1秒
</context>

<tasks>

<task type="auto">
  <name>Task 1: 修改 _split_into_short_messages 为20字限制并优化断点优先级</name>
  <files>backend/app/services/group_chat_service.py</files>
  <action>
修改 `_split_into_short_messages` 方法（大约在 line 246）:

1. 将 max_length 默认值从 80 改为 20
2. 优化断点优先级:
   - 第一优先级: 句号、问号、感叹号 (。！？) - 这些是完整的句子结束
   - 第二优先级: 逗号、顿号 (，、) - 句子中间的停顿
   - 第三优先级: 空格 - 英文单词分隔
3. 拆分逻辑调整:
   - 如果20字内找到句号/问号/感叹号，在该标点处拆分
   - 如果20字内找到逗号，在逗号后拆分
   - 如果20字内没有任何断点，强制在20字处拆分

实现逻辑示例:
```python
def _split_into_short_messages(self, text: str, max_length: int = 20) -> List[str]:
    if not text or len(text) <= max_length:
        return [text] if text else []

    messages = []
    current = ""

    # 断点优先级
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

    if current.strip():
        messages.append(current.strip())

    return messages
```
  </action>
  <verify>
    <automated>grep -n "def _split_into_short_messages" backend/app/services/group_chat_service.py && grep -n "max_length.*20" backend/app/services/group_chat_service.py</automated>
  </verify>
  <done>方法 max_length 默认为 20，断点优先级为 句号/问号/感叹号 > 逗号 > 强制截断</done>
</task>

<task type="auto">
  <name>Task 2: 在 router event_generator 中添加1秒延迟发送机制</name>
  <files>backend/app/routers/group_chat.py</files>
  <action>
在 `start_group_chat_stream` 和 `add_group_message_stream` 两个 endpoint 的 event_generator 中添加延迟发送逻辑:

修改位置大约在 line 210-218 (start_group_chat_stream) 和 line 331-337 (add_group_message_stream):

当前代码:
```python
# 后处理：去重和拆分
final_response, should_split = group_chat_service._deduplicate_and_split(full_response)

# 如果需要拆分，发送拆分信号
if should_split and final_response:
    short_messages = group_chat_service._split_into_short_messages(final_response)
    if len(short_messages) > 1:
        yield f"data: {json.dumps({'type': 'message_split', 'bot_name': bot.name, 'count': len(short_messages)})}\n\n"
```

修改为:
```python
# 后处理：去重和拆分
final_response, should_split = group_chat_service._deduplicate_and_split(full_response)

# 拆分为20字短消息
short_messages = group_chat_service._split_into_short_messages(final_response, max_length=20)

# 逐条发送短消息，每条间隔1秒
if len(short_messages) > 1:
    # 发送拆分信号
    yield f"data: {json.dumps({'type': 'message_split', 'bot_name': bot.name, 'count': len(short_messages)})}\n\n"

    # 逐条发送，每条间隔1秒
    for i, msg in enumerate(short_messages[1:], 1):
        yield f"data: {json.dumps({'type': 'chunk', 'bot_name': bot.name, 'content': msg, 'part': i+1, 'total_parts': len(short_messages)})}\n\n"
        await asyncio.sleep(1.0)  # 1秒间隔
else:
    # 不需要拆分时，原样发送
    if final_response:
        yield f"data: {json.dumps({'type': 'chunk', 'bot_name': bot.name, 'content': final_response})}\n\n"
```

注意: 需要在文件顶部确保已导入 asyncio (已导入)
  </action>
  <verify>
    <automated>grep -n "await asyncio.sleep(1.0)" backend/app/routers/group_chat.py</automated>
  </verify>
  <done>每条短消息发送间隔1秒，用户看到连续对话效果</done>
</task>

<task type="auto">
  <name>Task 3: 更新 auto_chat_rounds 使用新的20字拆分</name>
  <files>backend/app/services/group_chat_service.py</files>
  <action>
更新 `auto_chat_rounds` 函数中的短消息拆分逻辑（大约在 line 678）:

当前代码 (line 678):
```python
short_messages = service._split_into_short_messages(full_response, max_length=80)
```

修改为:
```python
short_messages = service._split_into_short_messages(full_response, max_length=20)
```

同时检查 line 706-708 的延迟逻辑:
```python
# 计算延迟：每条消息延迟 1-2 秒
delay = min(len(msg) * 0.05, 1.0) + 1.0
await asyncio.sleep(delay)
```

这个延迟计算已经包含了1秒基础延迟，可以保留。但为了统一使用固定1秒，可以改为:
```python
# 1秒固定间隔
await asyncio.sleep(1.0)
```
  </action>
  <verify>
    <automated>grep -n "max_length=20" backend/app/services/group_chat_service.py</automated>
  </verify>
  <done>auto_chat_rounds 也使用20字短消息拆分</done>
</task>

</tasks>

<verification>
- [ ] _split_into_short_messages 方法 max_length=20
- [ ] 断点优先级: 句号/问号/感叹号 > 逗号 > 强制截断
- [ ] event_generator 中有 await asyncio.sleep(1.0)
- [ ] auto_chat_rounds 使用 max_length=20
</verification>

<success_criteria>
1. 每条短消息≤20个汉字
2. 拆分优先在句号、问号、感叹号处
3. 多条消息间隔1秒发送
4. 用户在群聊中看到连续对话效果
</success_criteria>

<output>
After completion, create `.planning/phases/02-short-message/02-SUMMARY.md`
</output>
