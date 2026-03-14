---
phase: "01-stream-dedup"
plan: "01"
type: "execute"
wave: 1
depends_on: []
files_modified:
  - "backend/app/services/streaming_dedup.py"
  - "backend/app/services/llm_service.py"
  - "backend/app/services/group_chat_service.py"
autonomous: true
requirements:
  - "DEDUP-01"
  - "DEDUP-02"
  - "DEDUP-03"
user_setup: []
must_haves:
  truths:
    - "Users cannot see consecutive duplicate phrases (like 'hello hello') when watching bot conversations"
    - "Bot's consecutive output does not contain previously sent message fragments"
    - "Deduplication executes in real-time during streaming without affecting output latency"
    - "Users can send messages normally, bot responses have no obvious duplicate content"
  artifacts:
    - path: "backend/app/services/streaming_dedup.py"
      provides: "Stream dedup core classes: NGramDetector, BufferedDeduplicator, HistoryChecker"
      exports: ["NGramDetector", "BufferedDeduplicator", "HistoryChecker"]
    - path: "backend/app/services/llm_service.py"
      provides: "chat_stream method with stream dedup integration"
      contains: "use_stream_dedup"
    - path: "backend/app/services/group_chat_service.py"
      provides: "_generate_bot_response_stream with history checking"
      contains: "HistoryChecker"
  key_links:
    - from: "llm_service.chat_stream"
      to: "streaming_dedup.BufferedDeduplicator"
      via: "process_chunk() method"
      pattern: "await dedup.process_chunk"
    - from: "group_chat_service._generate_bot_response_stream"
      to: "streaming_dedup.HistoryChecker"
      via: "set_history_checker()"
      pattern: "history_checker.add_message"
---

<objective>
实现实时流式输出中的重复内容检测与过滤，确保用户看不到重复消息。

Purpose: 实现实时检测流式输出中的重复内容，在发送到前端前过滤，采用缓冲区批量去重方案，使用n-gram算法（n=4）
Output: 创建streaming_dedup模块，集成到llm_service和group_chat_service
</objective>

<execution_context>
@D:/0正事/学习资料/testforcc/.claude/get-shit-done/workflows/execute-plan.md
@D:/0正事/学习资料/testforcc/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@D:/0正事/学习资料/testforcc/.planning/phases/01-stream-dedup/01-CONTEXT.md
@D:/0正事/学习资料/testforcc/.planning/phases/01-stream-dedup/01-RESEARCH.md
@D:/0正事/学习资料/testforcc/backend/app/services/llm_service.py
@D:/0正事/学习资料/testforcc/backend/app/services/group_chat_service.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create streaming_dedup.py module with core classes</name>
  <files>backend/app/services/streaming_dedup.py</files>
  <action>
Create new module `backend/app/services/streaming_dedup.py` with three classes:

1. **NGramDetector** class:
   - `__init__(n=4, min_duplicate_count=2)` - n-gram size and minimum duplicates to detect
   - `extract_ngrams(text)` - Extract n-grams from text (character-level for Chinese)
   - `check_duplicate(text)` - Check if text contains consecutive duplicate n-grams
   - `get_unique_tail(text)` - Remove consecutive duplicate segments from text

2. **BufferedDeduplicator** class:
   - `__init__(buffer_size=100, flush_interval=0.05, n=4, min_duplicate_len=8)`
   - `set_history_checker(history_checker)` - Set history checker instance
   - `process_chunk(chunk)` - Process streaming chunk, returns deduplicated content when buffer flushes
   - `_flush()` - Internal flush with deduplication
   - `_deduplicate(text)` - Apply n-gram deduplication
   - `_remove_consecutive_duplicates(text, n)` - Remove consecutive duplicate n-grams
   - `flush_remaining()` - Flush any remaining content in buffer

3. **HistoryChecker** class:
   - `__init__(max_history=10)` - Maximum historical messages to keep
   - `add_message(message)` - Add sent message to history and extract n-grams
   - `filter_duplicate(text)` - Filter content that duplicates historical messages
   - `has_significant_duplicate(text, threshold=0.8)` - Check high similarity with history

Use collections.deque for sliding window. All methods must be async-compatible (or use asyncio if time-based flush needed).
  </action>
  <verify>
    <automated>python -c "from backend.app.services.streaming_dedup import NGramDetector, BufferedDeduplicator, HistoryChecker; print('Import OK')"</automated>
  </verify>
  <done>streaming_dedup.py module created with all three classes exported</done>
</task>

<task type="auto">
  <name>Task 2: Integrate deduplication into llm_service.py chat_stream</name>
  <files>backend/app/services/llm_service.py</files>
  <action>
Modify `llm_service.py` chat_stream method to integrate real-time deduplication:

1. Import BufferedDeduplicator: `from backend.app.services.streaming_dedup import BufferedDeduplicator`

2. Add `use_stream_dedup: bool = True` parameter to chat_stream method

3. Create deduplicator instance when enabled:
```python
dedup = BufferedDeduplicator(
    buffer_size=100,
    flush_interval=0.05,
    n=4
) if use_stream_dedup else None
```

4. In the streaming loop, wrap each chunk:
```python
async for text_chunk in stream.text_stream:
    if dedup:
        deduped = await dedup.process_chunk(text_chunk)
        if deduped:
            yield deduped
    else:
        yield text_chunk
```

5. After stream completes, flush remaining:
```python
if dedup:
    remaining = await dedup.flush_remaining()
    if remaining:
        yield remaining
```

Note: Keep existing `_deduplicate_text` method as fallback post-processing.
  </action>
  <verify>
    <automated>python -c "from backend.app.services.llm_service import LLMService; print('LLMService import OK')"</automated>
  </verify>
  <done>chat_stream method now processes chunks through BufferedDeduplicator when use_stream_dedup=True</done>
</task>

<task type="auto">
  <name>Task 3: Integrate history checking into group_chat_service.py</name>
  <files>backend/app/services/group_chat_service.py</files>
  <action>
Modify `group_chat_service.py` _generate_bot_response_stream method to integrate history checking:

1. Import classes:
```python
from backend.app.services.streaming_dedup import BufferedDeduplicator, HistoryChecker
```

2. In _generate_bot_response_stream method, create HistoryChecker with previous bot messages:
```python
history_checker = HistoryChecker(max_history=10)

# Add previous bot responses to history
for msg in all_messages:
    if msg.get("sender_name") == bot.name:
        history_checker.add_message(msg.get("content", ""))
```

3. Create BufferedDeduplicator with history checker:
```python
dedup = BufferedDeduplicator(
    buffer_size=100,
    flush_interval=0.05,
    n=4
)
dedup.set_history_checker(history_checker)
```

4. Modify the streaming call to use stream_dedup=True and apply additional inline deduplication:
```python
async for text_chunk in llm_service.chat_stream(
    messages=messages,
    system_prompt=system_prompt,
    temperature=bot.temperature,
    max_tokens=bot.max_tokens,
    use_stream_dedup=True  # Enable streaming dedup
):
    # Additional inline deduplication for immediate chunks
    cleaned = dedup.ngram_detector.get_unique_tail(text_chunk)
    if cleaned:
        yield cleaned

# After streaming, add final message to history
if full_response:
    history_checker.add_message(full_response)
```

Note: Ensure full_response is accumulated during streaming to update history at the end.
  </action>
  <verify>
    <automated>python -c "from backend.app.services.group_chat_service import GroupChatService; print('GroupChatService import OK')"</automated>
  </verify>
  <done>_generate_bot_response_stream now uses HistoryChecker to prevent repeating previous bot messages</done>
</task>

</tasks>

<verification>
Overall phase checks:
1. streaming_dedup.py module imports successfully
2. llm_service.py chat_stream accepts use_stream_dedup parameter
3. group_chat_service.py integrates HistoryChecker
4. All three requirements (DEDUP-01, DEDUP-02, DEDUP-03) addressed
</verification>

<success_criteria>
Measurable completion:
1. Users cannot see consecutive duplicate phrases when watching bot conversations
2. Bot output does not contain previously sent message fragments
3. Deduplication executes in real-time during streaming
4. Users can send messages normally, bot responses have no obvious duplicates
</success_criteria>

<output>
After completion, create `.planning/phases/01-stream-dedup/01-01-SUMMARY.md`
</output>
