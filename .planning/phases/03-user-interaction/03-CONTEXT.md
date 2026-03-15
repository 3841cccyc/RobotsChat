# Phase 3: 用户互动机制 - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

实现用户可以通过@提及机器人或@所有人来参与对话，触发机器人响应

Requirements:
- USER-01: 用户@提及机制，支持@特定机器人或@所有人
- USER-02: 用户消息触发机器人响应流程

</domain>

<decisions>
## Implementation Decisions

### 触发机制
- **任意消息触发**：用户发送任何消息时机器人都可能响应
- 机器人与用户的交互不再是单向的，而是可以自然地参与讨论
- 与现有的 auto_chat_rounds 机制协同工作

### @识别方式
- **模糊匹配**：支持@机器人名或@all，不区分大小写
- 例如: "@小爱", "@小爱 ", "@ALL", "@all" 都应该被识别
- 正则表达式模式: r'@(\w+)' 或 r'@all'

### 多机器人响应
- **全部响应**：所有被@的机器人都响应
- 用户可以看到不同机器人的观点碰撞
- 如果没有@具体机器人但有用户消息，也触发所有机器人（配合任意消息触发）

### 与现有系统集成
- 复用现有的 group_chat_service.py 的消息处理流程
- 在消息解析阶段添加 @mention 检测逻辑
- 检测到@后，更新触发机器人的列表

</decisions>

<specifics>
## Specific Ideas

- 在 `add_user_message_stream` 方法中，在保存用户消息后检测@mentions
- 如果检测到@，只让被@的机器人响应；如果没有@但有用户消息，让所有机器人响应
- 前端需要显示@提及的解析结果（哪些机器人被@）
- 支持 @all 或 @所有人 触发所有机器人

</specifics>

{#code_context}
## Existing Code Insights

### Reusable Assets
- `group_chat_service.py`:
  - `add_user_message_stream` - 用户消息处理入口，需要在此添加@检测
  - `auto_chat_rounds` - 现有的自动对话轮次逻辑
  - `_get_bot_context` - 获取机器人上下文

### Integration Points
- `group_chat_service.py` 的 `add_user_message_stream` 方法（约 line 481）
- 需要在处理用户消息时添加 @mention 解析逻辑
- 根据解析结果决定哪些机器人需要响应

### Current Behavior
- 当前用户消息会触发机器人响应（通过 add_user_message_stream）
- 但没有@mention 的解析和筛选机制
- 所有机器人都会响应用户消息

</code_context>

<deferred>
## Deferred Ideas

- Phase 2 (v2): @机器人智能回复（基于关键词相关性选择）- 未来可能的需求
- 富媒体消息（表情、图片）- 不在当前phase范围内

</deferred>

---

*Phase: 03-user-interaction*
*Context gathered: 2026-03-15*
