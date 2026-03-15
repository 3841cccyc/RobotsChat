# Phase 2: 短消息输出 - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

将长输出截断为≤20字/条的短消息，在合理断点拆分，实现连续输出效果

Requirements:
- SHORT-01: 截断长输出为 ≤20字/条 的短消息
- SHORT-02: 在合理断点（句号、逗号、问号）拆分消息
- SHORT-03: 实现连续输出效果，每条短消息间隔发送

</domain>

<decisions>
## Implementation Decisions

### 截断时机
- **采用事后拆分方案**：先生成完整回复，然后拆分成20字短消息
- 理由：用户选择此方案，简化实现复杂度

### 断点优先级
- **优先自然断点**：句号(。)、问号(？)、感叹号(！)优先
- 如果20字内没有自然断点，则强制在20字处截断

### 发送间隔
- **1秒间隔**：每条短消息发送后等待1秒再发送下一条
- 理由：用户选择"适中"速度，模拟人类打字速度

### 与去重模块的关系
- 复用 streaming_dedup 模块的 HistoryChecker
- 去重在先（生成完整回复后），截断在后
- 短消息拆分作为独立功能模块实现

</decisions>

<specifics>
## Specific Ideas

- 修改现有的 `_split_into_short_messages` 方法，将 max_length 从 80 改为 20
- 调整断点优先级：句号、问号、感叹号 > 逗号、顿号 > 强制截断
- 在 router 的 event_generator 中添加延迟机制实现1秒间隔
- 确保拆分后的短消息不包含重复内容

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `group_chat_service.py`:
  - `_split_into_short_messages(text, max_length=80)` - 现有拆分方法，需要修改为20
  - `_deduplicate_and_split(text, previous_content)` - 现有去重+拆分方法
- `streaming_dedup.py`:
  - `HistoryChecker` - 可复用于检测历史消息重复

### Integration Points
- `group_chat_service.py` 的 `_generate_bot_response_stream` 方法
- `group_chat.py` 的 `event_generator` 函数中的 yield 位置
- 需要在完整响应生成后、短消息发送前添加延迟

### Current Behavior
- 当前 max_length=80，不是20
- 当前是在完整响应后一次性拆分，不是流式发送多条

</code_context>

<deferred>
## Deferred Ideas

- Phase 3 会讨论 @提及机制
- 流式实时截断方案（用户未选择，但可作为未来优化方向）

</deferred>

---

*Phase: 02-short-message*
*Context gathered: 2026-03-15*
