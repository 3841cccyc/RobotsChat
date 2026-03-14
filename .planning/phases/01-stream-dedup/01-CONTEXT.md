# Phase 1: 流式去重核心 - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

实时检测流式输出中的重复内容，在发送到前端前过滤，确保用户看不到重复消息。

Requirements:
- DEDUP-01: 实时检测流式输出中的重复内容，在发送到前端前过滤
- DEDUP-02: 基于 n-gram 的去重算法，过滤连续重复短语
- DEDUP-03: 与历史消息比对，防止重复已发送内容

</domain>

<decisions>
## Implementation Decisions

### 去重策略
- 采用实时流式去重方案
- 在流式输出过程中实时检测并过滤重复内容
- 用户看不到任何重复内容

### 实现方式
- 缓冲区批量去重 (Buffered Deduplicator)
- 收集一定量内容后批量去重再推送到前端
- 平衡实时性和去重效果

### 检测算法
- 滑动窗口 n-gram 算法
- n 值选择: 4

</decisions>

<specifics>
## Specific Ideas

- 用户明确要求：流式输出过程中实时去重，不能让用户看到重复内容
- 用户选择了缓冲区方案来平衡性能和效果

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `llm_service.py`: `_deduplicate_text` - 12轮事后去重算法，可参考
- `group_chat_service.py`: `_deduplicate_response`, `_deduplicate_and_split` - 现有去重方法
- `auto_chat_rounds`: 现有流式输出框架

### Established Patterns
- SSE 流式输出: `StreamingResponse` with event stream
- 异步生成器模式: `async for chunk in llm_service.chat_stream()`

### Integration Points
- `llm_service.py` 的 `chat_stream` 方法
- `group_chat_service.py` 的 `_generate_bot_response_stream` 方法
- 需要修改流式输出管道，在发送前加入去重处理

</code_context>

<deferred>
## Deferred Ideas

- Phase 2 会讨论 20字短消息截断
- Phase 3 会讨论 @提及机制

</deferred>

---

*Phase: 01-stream-dedup*
*Context gathered: 2026-03-14*
