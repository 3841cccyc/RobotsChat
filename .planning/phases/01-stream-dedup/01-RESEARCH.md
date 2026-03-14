# Phase 1: 流式去重核心 - Research

**Researched:** 2026-03-14
**Domain:** Real-time stream text deduplication, n-gram algorithm, async streaming
**Confidence:** HIGH

## Summary

This phase implements real-time deduplication for streaming LLM output. The project already has post-processing deduplication in `llm_service.py` (`_deduplicate_text` - 12 rounds) and `group_chat_service.py` (`_deduplicate_response`). The new requirement is to detect and filter duplicate content **during** streaming, before sending to the frontend.

**Primary recommendation:** Implement a `BufferedDeduplicator` class with sliding window n-gram algorithm (n=4), integrated into the streaming pipeline at `llm_service.chat_stream()` and `group_chat_service._generate_bot_response_stream()`.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Real-time streaming deduplication (not post-processing)
- Buffered Deduplicator approach
- Sliding window n-gram algorithm, n=4
- Integration points: `llm_service.py` chat_stream method, `group_chat_service.py` _generate_bot_response_stream method

### Claude's Discretion
- Buffer size configuration
- Flush interval timing
- Whether to reuse existing `_deduplicate_text` logic in the buffer flush

### Deferred Ideas (OUT OF SCOPE)
- Phase 2 will handle 20-character short message truncation
- Phase 3 will handle @mention mechanism

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEDUP-01 | 实时检测流式输出中的重复内容，在发送到前端前过滤 | BufferedDeduplicator with n-gram detection |
| DEDUP-02 | 基于 n-gram 的去重算法，过滤连续重复短语 | Sliding window n-gram (n=4) implementation |
| DEDUP-03 | 与历史消息比对，防止重复已发送内容 | History comparison with sent messages |

## Standard Stack

### Core Technologies
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python asyncio | 3.10+ | Async streaming | Native async generator support, project already uses it |
| re (regex) | stdlib | Pattern matching | Already used in existing `_deduplicate_text`, proven effective |
| collections.deque | stdlib | Sliding window buffer | Memory-efficient for fixed-size window |

### No External Dependencies Required
This implementation uses only Python standard library, leveraging existing project patterns.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/services/
├── llm_service.py              # Existing - keep as-is
├── group_chat_service.py       # Existing - modify for integration
├── streaming_dedup.py          # NEW: Stream deduplication module
│   ├── BufferedDeduplicator    # Main deduplicator class
│   ├── NGramDetector          # N-gram detection logic
│   └── HistoryChecker          # History comparison (DEDUP-03)
└── __init__.py
```

### Pattern 1: Buffered Deduplicator (Primary Approach)

**What:** Collect streaming chunks in a buffer, apply deduplication when buffer reaches threshold or flush interval triggers.

**When to use:** When balancing real-time responsiveness with effective deduplication (user's chosen approach).

**Implementation:**
```python
# Source: Based on project patterns + STACK.md recommended approach
import asyncio
import re
from collections import deque
from typing import AsyncGenerator, Optional, List, Set

class NGramDetector:
    """N-gram based duplicate detector for streaming text"""

    def __init__(self, n: int = 4, min_duplicate_count: int = 2):
        self.n = n
        self.min_duplicate_count = min_duplicate_count
        self.seen_ngrams: Set[str] = set()
        self.recent_ngrams: deque = deque(maxlen=100)  # Sliding window

    def extract_ngrams(self, text: str) -> List[str]:
        """Extract n-grams from text"""
        ngrams = []
        # Handle both Chinese and English characters
        # For Chinese: treat each character as a unit
        # For English: treat words as units
        text = text.strip()
        if len(text) < self.n:
            return ngrams

        # Character-level n-grams (works for Chinese)
        for i in range(len(text) - self.n + 1):
            ngram = text[i:i + self.n]
            ngrams.append(ngram)

        return ngrams

    def check_duplicate(self, text: str) -> bool:
        """Check if text contains duplicate n-grams (consecutive repetition)"""
        ngrams = self.extract_ngrams(text)
        if len(ngrams) < self.min_duplicate_count:
            return False

        # Check for consecutive duplicate n-grams
        for i in range(len(ngrams) - 1):
            if ngrams[i] == ngrams[i + 1]:
                return True

        return False

    def get_unique_tail(self, text: str) -> str:
        """Get the unique portion of text by removing consecutive duplicates"""
        if len(text) < self.n:
            return text

        # Check from the end - find where repetition starts
        for i in range(len(text) - self.n, -1, -1):
            # Check if current position starts a repeated segment
            segment = text[i:i + self.n]
            # Look for the segment before current position
            if i >= self.n:
                prev_segment = text[i - self.n:i]
                if segment == prev_segment:
                    # Found repetition, return up to the start of repetition
                    return text[:i]

        return text


class BufferedDeduplicator:
    """
    Buffered deduplicator for real-time stream processing.
    Collects chunks in buffer, deduplicates on flush.
    """

    def __init__(
        self,
        buffer_size: int = 100,        # Characters to collect before flush
        flush_interval: float = 0.05,  # Seconds (50ms)
        n: int = 4,                    # N-gram size
        min_duplicate_len: int = 8     # Minimum chars to check
    ):
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.n = n
        self.min_duplicate_len = min_duplicate_len

        self.buffer = ""
        self.ngram_detector = NGramDetector(n=n)
        self.history_checker: Optional[HistoryChecker] = None

    def set_history_checker(self, history_checker: 'HistoryChecker'):
        """Set the history checker for DEDUP-03"""
        self.history_checker = history_checker

    async def process_chunk(self, chunk: str) -> Optional[str]:
        """
        Process a single chunk from the stream.
        Returns deduplicated content if buffer should flush, None otherwise.
        """
        self.buffer += chunk

        # Only process when buffer is large enough
        if len(self.buffer) < self.min_duplicate_len:
            return None

        # Check if buffer should flush
        should_flush = len(self.buffer) >= self.buffer_size

        if should_flush:
            return await self._flush()

        return None

    async def _flush(self) -> str:
        """Flush buffer with deduplication"""
        if not self.buffer:
            return ""

        # Apply n-gram deduplication
        result = self._deduplicate(self.buffer)

        # Check against history (DEDUP-03)
        if self.history_checker and result:
            result = self.history_checker.filter_duplicate(result)

        self.buffer = ""
        return result

    def _deduplicate(self, text: str) -> str:
        """Apply n-gram based deduplication"""
        # Remove consecutive duplicate n-grams at chunk boundaries
        result = text

        # Use sliding window to find and remove repeated segments
        for n in range(self.n, self.n + 3):  # Check n, n+1, n+2
            result = self._remove_consecutive_duplicates(result, n)

        return result

    def _remove_consecutive_duplicates(self, text: str, n: int) -> str:
        """Remove consecutive duplicate n-grams"""
        if len(text) < n * 2:
            return text

        result = text
        max_iterations = 10  # Prevent infinite loop

        for _ in range(max_iterations):
            original = result
            ngrams = []

            # Extract n-grams
            for i in range(len(result) - n + 1):
                ngrams.append(result[i:i + n])

            # Find consecutive duplicates and remove second occurrence
            new_chars = []
            skip_next = False

            for i, ngram in enumerate(ngrams):
                if skip_next:
                    skip_next = False
                    continue

                # Check if this n-gram is same as next
                if i + 1 < len(ngrams) and ngram == ngrams[i + 1]:
                    # Skip the duplicate
                    skip_next = True
                    # Also skip the characters in result
                    new_chars.append(result[i])
                    continue

                new_chars.append(result[i])

            # Add remaining characters
            if len(ngrams) > 0:
                # Add last character if not added
                last_idx = len(result) - 1
                if last_idx >= len(ngrams):
                    new_chars.append(result[last_idx])

            result = "".join(new_chars)

            if result == original:
                break

        return result

    async def flush_remaining(self) -> str:
        """Flush any remaining content in buffer"""
        if self.buffer:
            result = self._deduplicate(self.buffer)
            if self.history_checker and result:
                result = self.history_checker.filter_duplicate(result)
            self.buffer = ""
            return result
        return ""


class HistoryChecker:
    """Check against historical messages to prevent repetition (DEDUP-03)"""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.sent_messages: List[str] = []
        self.sent_ngrams: Set[str] = set()

    def add_message(self, message: str):
        """Add a sent message to history"""
        self.sent_messages.append(message)

        # Extract n-grams for faster comparison
        detector = NGramDetector(n=4)
        ngrams = detector.extract_ngrams(message)
        self.sent_ngrams.update(ngrams)

        # Trim history if too large
        if len(self.sent_messages) > self.max_history:
            self.sent_messages = self.sent_messages[-self.max_history:]

    def filter_duplicate(self, text: str) -> str:
        """Filter content that duplicates historical messages"""
        if not text or not self.sent_messages:
            return text

        # Check if text starts with any historical message
        for history_msg in self.sent_messages:
            if text.startswith(history_msg):
                # Remove the duplicated prefix
                text = text[len(history_msg):]

        return text

    def has_significant_duplicate(self, text: str, threshold: float = 0.8) -> bool:
        """Check if text has high similarity with history"""
        if not text or not self.sent_messages:
            return False

        # Simple length-based quick check
        for history_msg in self.sent_messages:
            # If there's significant overlap, flag it
            if len(text) > 20 and len(history_msg) > 20:
                # Count matching characters
                matches = sum(1 for a, b in zip(text, history_msg) if a == b)
                overlap = matches / max(len(text), len(history_msg))
                if overlap > threshold:
                    return True

        return False
```

### Pattern 2: Integration with Streaming Pipeline

**Integration Point 1: llm_service.py chat_stream**
```python
# Modify chat_stream to use real-time deduplication
async def chat_stream(
    self,
    messages: List[Dict[str, str]],
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    learned_context: str = "",
    use_stream_dedup: bool = True  # New parameter
) -> AsyncGenerator[str, None]:
    """流式对话 with real-time deduplication"""

    # Get LLM response stream (real streaming from API)
    client = self._get_client()
    # ... (setup messages)

    # Create deduplicator if enabled
    dedup = BufferedDeduplicator(
        buffer_size=100,
        flush_interval=0.05,
        n=4
    ) if use_stream_dedup else None

    # Stream from LLM with real-time deduplication
    async with client.messages.stream(
        model=self.model,
        max_tokens=max_tokens,
        system=full_system,
        messages=anthropic_messages,
        temperature=temperature
    ) as stream:
        async for text_chunk in stream.text_stream:
            if dedup:
                deduped = await dedup.process_chunk(text_chunk)
                if deduped:
                    yield deduped
            else:
                yield text_chunk

    # Flush remaining
    if dedup:
        remaining = await dedup.flush_remaining()
        if remaining:
            yield remaining
```

**Integration Point 2: group_chat_service.py _generate_bot_response_stream**
```python
async def _generate_bot_response_stream(
    self,
    bot: Bot,
    messages: List[Dict],
    all_messages: List[Dict],
) -> AsyncGenerator[str, None]:
    """流式生成机器人回复 with real-time deduplication"""

    # Setup system prompt (existing code)...

    # Create history checker for this bot's responses
    history_checker = HistoryChecker(max_history=10)

    # Add previous bot responses to history
    for msg in all_messages:
        if msg.get("sender_name") == bot.name:
            history_checker.add_message(msg.get("content", ""))

    # Create deduplicator with history checker
    dedup = BufferedDeduplicator(
        buffer_size=100,
        flush_interval=0.05,
        n=4
    )
    dedup.set_history_checker(history_checker)

    # Stream with deduplication
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
```

### Anti-Patterns to Avoid
- **Pure character-by-character deduplication:** Too aggressive, breaks words
- **No buffer (instant dedup):** Loses context for detecting longer repeats
- **Ignoring history (DEDUP-03):** Only catches immediate repeats, not repeats of previous messages
- **Synchronous deduplication in async stream:** Blocks the event loop

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async stream handling | Custom async queue | Python async generators | Native FastAPI support |
| N-gram extraction | Custom sliding window | `collections.deque` with maxlen | Memory efficient, proven |
| Pattern matching | Custom regex | Python `re` module | Already in project, proven effective |
| Text similarity | Complex ML similarity | Simple prefix/suffix matching | Fast, sufficient for this use case |

## Common Pitfalls

### Pitfall 1: Buffer Boundary Duplicates
**What goes wrong:** Duplicates occur at buffer flush boundaries.
**Why it happens:** When buffer flushes, the transition between buffers can contain partial repeated segments.
**How to avoid:** Use `get_unique_tail()` to check chunk endings for partial repeats.
**Warning signs:** User sees repeated 4-8 character phrases at inconsistent positions.

### Pitfall 2: Chinese Character Handling
**What goes wrong:** N-gram treats each character, but Chinese has different semantics.
**Why it happens:** Character-level n-grams work but may not capture word boundaries.
**How to avoid:** Use n=4 which is 4 Chinese characters, good for detecting phrase repetition.
**Warning signs:** Very short repeats (1-2 chars) or missed longer repeats.

### Pitfall 3: History Not Updated
**What goes wrong:** DEDUP-03 fails because history checker isn't updated with sent messages.
**Why it happens:** Integration point misses calling `history_checker.add_message()`.
**How to avoid:** Ensure `_generate_bot_response_stream` adds completed messages to history before yielding done signal.
**Warning signs:** Bot repeats exact phrases from previous turns.

### Pitfall 4: Buffer Never Flushes
**What goes wrong:** Small chunks never reach buffer_size threshold.
**Why it happens:** LLM streams very slowly or with small chunks.
**How to avoid:** Use time-based flush in addition to size-based: `flush_interval`.
**Warning signs:** Long delay before first output appears.

## Code Examples

### Example 1: N-gram Detection in Action
```python
# Source: Based on NGramDetector class
detector = NGramDetector(n=4)

# Test cases
test_cases = [
    "你好呀你好呀",      # Consecutive repeat
    "今天天气很好今天天气很好",  # Longer repeat
    "这是一个正常的句子",  # No repeat
    "嘿嘿嘿嘿",          # Character repeat
]

for text in test_cases:
    has_dup = detector.check_duplicate(text)
    unique = detector.get_unique_tail(text)
    print(f"Input: {text}")
    print(f"  Has duplicate: {has_dup}")
    print(f"  Unique tail: {unique}")
    print()
```

### Example 2: Buffered Processing Flow
```python
# Source: Based on BufferedDeduplicator
async def example_usage():
    dedup = BufferedDeduplicator(buffer_size=50, n=4)

    # Simulate streaming chunks
    chunks = ["今天", "天气", "很好", "很好", "，", "我们", "我们", "去", "去", "玩吧"]

    results = []
    async for chunk in async_generator_from_llm(chunks):
        result = await dedup.process_chunk(chunk)
        if result:
            results.append(result)

    # Flush remaining
    remaining = await dedup.flush_remaining()
    if remaining:
        results.append(remaining)

    print("Deduplicated output:", "".join(results))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Post-processing dedup only | Real-time stream dedup | Phase 1 (current) | User sees no duplicates during streaming |
| 12-round regex in `_deduplicate_text` | 4-gram sliding window | Phase 1 | Lighter computation, real-time |

**Deprecated/outdated:**
- Pure post-processing deduplication: Will be superseded by real-time approach but kept as fallback
- Simulated streaming (current `chat_stream`): Will be replaced with real streaming from LLM API

## Open Questions

1. **Buffer Size Configuration**
   - What we know: User chose "buffered" approach, typical values 50-200 chars
   - What's unclear: Optimal balance for this project's LLM response size
   - Recommendation: Start with 100 chars, tune based on testing

2. **Integration with Real LLM Streaming**
   - What we know: Current `chat_stream` gets full response first, then simulates streaming
   - What's unclear: Whether MiniMax API streaming is available/reliable
   - Recommendation: Modify to use real streaming API if possible, or keep simulated with dedup

3. **Performance Under High Load**
   - What we know: Project uses async, but dedup adds processing per chunk
   - What's unclear: Impact on response time with multiple concurrent conversations
   - Recommendation: Profile after implementation, consider batching if needed

## Validation Architecture

> Skip this section entirely if workflow.nyquist_validation is explicitly set to false in .planning/config.json. If the key is absent, treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pytest.ini (check if exists) |
| Quick run command | `pytest tests/test_streaming_dedup.py -x -v` |
| Full suite command | `pytest tests/ -x -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEDUP-01 | Real-time duplicate detection | unit + integration | `pytest tests/test_streaming_dedup.py::test_buffered_dedup_basic -x` | Need to create |
| DEDUP-02 | N-gram algorithm n=4 | unit | `pytest tests/test_streaming_dedup.py::test_ngram_detector -x` | Need to create |
| DEDUP-03 | History comparison | unit | `pytest tests/test_streaming_dedup.py::test_history_checker -x` | Need to create |

### Sampling Rate
- **Per task commit:** Run specific test for the feature
- **Per wave merge:** Full test suite
- **Phase gate:** All streaming dedup tests green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_streaming_dedup.py` — covers DEDUP-01, DEDUP-02, DEDUP-03
- [ ] `tests/conftest.py` — shared fixtures (check if exists)
- [ ] Framework install: `pip install pytest pytest-asyncio` — if not in requirements

*(If no gaps: "None — existing test infrastructure covers all phase requirements")*

## Sources

### Primary (HIGH confidence)
- Project existing code: `backend/app/services/llm_service.py` - `_deduplicate_text` method (12-round regex deduplication)
- Project existing code: `backend/app/services/group_chat_service.py` - `_deduplicate_response`, `_deduplicate_and_split` methods
- STACK.md - Recommended streaming deduplication patterns

### Secondary (MEDIUM confidence)
- Python asyncio documentation - Async generator patterns
- Python re module - Pattern matching (already proven in project)

### Tertiary (LOW confidence)
- Web search failed due to API error; relying on existing project patterns and standard library

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using Python stdlib only, proven patterns from project
- Architecture: HIGH - Based on STACK.md recommendations and project integration points
- Pitfalls: MEDIUM - Identified from project patterns and common streaming issues

**Research date:** 2026-03-14
**Valid until:** 90 days - Algorithm is stable, no external dependencies
