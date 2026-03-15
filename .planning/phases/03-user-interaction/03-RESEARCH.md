# Phase 3: 用户互动机制 (User Interaction Mechanism) - Research

**Researched:** 2026-03-15
**Domain:** Chat bot @mention detection, message trigger filtering
**Confidence:** HIGH

## Summary

This phase implements user interaction via @mentions. Users can trigger bot responses by mentioning specific bots (e.g., "@小爱") or "@all"/"@所有人" to trigger all bots. The key implementation is adding @mention detection logic in the `add_user_message_stream` method, parsing user messages to identify mentioned bots, and filtering which bots should respond.

**Primary recommendation:** Implement @mention detection as a pre-processing step in `group_chat_service.py`, using regex pattern `r'@(\w+)'` for bot mentions and checking for "@all"/"@所有人" variants. Filter the bot list passed to response generation based on detected mentions.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **触发机制**: 任意消息触发（用户发送任何消息时机器人都可能响应）
- **@识别**: 模糊匹配（支持@机器人名或@all，不区分大小写），正则表达式模式: `r'@(\w+)'` 或 `r'@all'`
- **多机器人响应**: 全部响应（所有被@的机器人都响应）

### Claude's Discretion
- 具体实现位置和代码结构
- 前端@提及显示格式

### Deferred Ideas (OUT OF SCOPE)
- Phase 2 (v2): @机器人智能回复（基于关键词相关性选择）
- 富媒体消息（表情、图片）
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| USER-01 | 用户@提及机制，支持@特定机器人或@所有人 | Regex pattern `r'@(\w+)'` for extracting mentions, case-insensitive matching against bot names |
| USER-02 | 用户消息触发机器人响应流程 | Filter bots by mentions in `add_user_message_stream`, default to all bots if no @mentions found |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `re` | built-in | @mention regex matching | Standard library, reliable for pattern extraction |
| SQLAlchemy | latest | Async database session | Already used in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio | built-in | Async operations | Already in use |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom parsing | `at` library | Python `re` is simpler for this use case |
| Exact match only | Fuzzy matching (regex) | Fuzzy is required by context decision |

**Installation:**
No new packages required - uses built-in Python `re` module.

---

## Architecture Patterns

### Recommended Project Structure
```
backend/app/services/
├── group_chat_service.py    # Add mention detection here
└── streaming_dedup.py       # Existing - no changes needed
```

### Pattern 1: @Mention Detection with Regex
**What:** Parse user messages to extract @mentions and match against bot names
**When to use:** When processing user messages in group chat
**Example:**
```python
import re

def detect_mentions(message: str, bots: List[Bot]) -> List[Bot]:
    """
    Detect @mentions in user message and return list of mentioned bots.
    Supports: @botname (case-insensitive), @all, @所有人
    """
    # Extract all @mentions using regex
    mention_pattern = r'@(\w+)'
    mentions = re.findall(mention_pattern, message, re.IGNORECASE)

    if not mentions:
        # No @mentions found - all bots respond (per context decision)
        return bots

    # Check for @all or @所有人
    all_keywords = {'all', 'everyone', '所有人', '大家'}
    if any(m.lower() in all_keywords for m in mentions):
        return bots

    # Filter bots by mentioned names (case-insensitive)
    mentioned_bots = []
    for bot in bots:
        for mention in mentions:
            if bot.name.lower() == mention.lower():
                mentioned_bots.append(bot)
                break

    return mentioned_bots if mentioned_bots else bots
```

### Pattern 2: Integration with add_user_message_stream
**What:** Insert mention detection before bot response generation
**When to use:** In the existing `add_user_message_stream` method
**Example:**
```python
# In add_user_message_stream, after saving user message
# Detect @mentions and filter bots
mentioned_bots = detect_mentions(user_prompt, bots)

# Only let mentioned bots respond
for bot in mentioned_bots:
    # ... existing response generation logic
```

### Anti-Patterns to Avoid
- **Case-sensitive matching:** Must use `re.IGNORECASE` flag per context decision
- **Only matching exact names:** Fuzzy matching required per context ("@小爱" should match bot "小爱")
- **Empty bot list on no mentions:** Per context, if no @mentions found, all bots should respond

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mention parsing | Custom tokenizer | `re.findall(r'@(\w+)', text)` | Simple, reliable, handles all cases |
| Case-insensitive matching | Multiple comparisons | `re.IGNORECASE` flag | Built-in, efficient |

**Key insight:** Regex is sufficient for @mention detection in this context. No need for NLP or complex parsing libraries.

---

## Common Pitfalls

### Pitfall 1: Bot Name Collision
**What goes wrong:** Bot "小爱" and user "@小爱爱" both match incorrectly
**Why it happens:** Partial substring matching instead of exact match
**How to avoid:** Use exact case-insensitive match: `if bot.name.lower() == mention.lower()`
**Warning signs:** Wrong bot responds to similar names

### Pitfall 2: Unicode Characters in Mentions
**What goes wrong:** "@所有人" doesn't match with regex `\w+` which doesn't match Chinese
**Why it happens:** `\w` in Python regex only matches `[a-zA-Z0-9_]`, not Chinese characters
**How to avoid:** Add explicit check for Chinese keywords or use Unicode-aware pattern `r'@([\w\u4e00-\u9fff]+)'`
**Warning signs:** "@所有人" or "@ALL" not detected

### Pitfall 3: Message Without @Mention Triggers All Bots (Unexpected)
**What goes wrong:** Per context, no @ should trigger all bots, but this might surprise users expecting no response
**Why it happens:** This is the locked decision - any message triggers response
**How to avoid:** This is by design per context decisions
**Warning signs:** Users expect bots to stay silent without @

---

## Code Examples

### Integration Point: group_chat_service.py

**File:** `backend/app/services/group_chat_service.py`
**Method:** `add_user_message_stream` (line ~481)

```python
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

    # ===== NEW: Detect @mentions =====
    # If @mentions found, only those bots respond; otherwise all bots respond
    responding_bots = self._filter_bots_by_mentions(user_prompt, bots)
    # ================================

    # ... existing code ...
    # Replace "for bot in bots:" with "for bot in responding_bots:"

    # Save user message
    user_message = GroupMessage(...)
    # ... rest unchanged
```

### New Method: _filter_bots_by_mentions

```python
def _filter_bots_by_mentions(self, message: str, bots: List[Bot]) -> List[Bot]:
    """
    Filter bots based on @mentions in message.

    Args:
        message: User's message content
        bots: List of all available bots

    Returns:
        List of bots that should respond (mentioned bots or all if no mentions)
    """
    if not message or not bots:
        return bots

    # Extract @mentions with support for Unicode (Chinese characters)
    # Pattern matches @ followed by word chars OR Chinese chars
    mention_pattern = r'@([a-zA-Z0-9_\u4e00-\u9fff]+)'
    mentions = re.findall(mention_pattern, message, re.IGNORECASE)

    if not mentions:
        # No @mentions - all bots respond (per context decision)
        return bots

    # Check for @all / @所有人 / @大家 (case-insensitive)
    all_keywords = {'all', 'everyone', '所有人', '大家', 'everyone'}
    normalized_mentions = {m.lower() for m in mentions}

    if normalized_mentions & all_keywords:  # Intersection check
        return bots

    # Filter bots by mentioned names (exact match, case-insensitive)
    mentioned_bots = []
    for bot in bots:
        for mention in mentions:
            if bot.name.lower() == mention.lower():
                mentioned_bots.append(bot)
                break

    # If no valid bots mentioned, all bots respond
    return mentioned_bots if mentioned_bots else bots
```

### Frontend: Display Mentions (Optional Enhancement)

When displaying user messages, show which bots were mentioned:

```python
# In the message display logic
mentioned_names = [m for m in re.findall(r'@(\w+)', message) if m.lower() != 'all']
# Highlight or tag these in UI
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All bots always respond | @mention filtering | This phase | Users can target specific bots |
| Exact name matching only | Fuzzy/case-insensitive matching | This phase | Better UX "@小爱" matches "小爱" |

**Deprecated/outdated:**
- None relevant to this phase

---

## Open Questions

1. **Should @mentions be stored in the database?**
   - What we know: Current schema doesn't have mention field
   - What's unclear: Whether analytics on which bots are most mentioned would be useful
   - Recommendation: Store as part of message metadata in future phase

2. **Should bot respond if mentioned in a reply chain?**
   - What we know: Context says "任意消息触发"
   - What's unclear: Should @mention in quoted/replied message count?
   - Recommendation: For v1, treat all user messages equally (current decision)

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already in project) |
| Config file | pytest.ini or pyproject.toml |
| Quick run command | `pytest tests/test_group_chat.py -x -v` |
| Full suite command | `pytest tests/ -x --tb=short` |

### Phase Requirements Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| USER-01 | @mention detection - specific bot | unit | `pytest tests/test_mention.py::test_specific_bot_mention -x` | No - need to create |
| USER-01 | @mention detection - @all | unit | `pytest tests/test_mention.py::test_all_mention -x` | No - need to create |
| USER-01 | Case insensitive matching | unit | `pytest tests/test_mention.py::test_case_insensitive -x` | No - need to create |
| USER-02 | Response flow with mentions | integration | `pytest tests/test_group_chat.py::test_user_message_with_mention -x` | No - need to create |

### Sampling Rate
- **Per task commit:** Unit tests for mention detection
- **Per wave merge:** Integration tests for full flow
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_mention.py` - unit tests for _filter_bots_by_mentions method
- [ ] `tests/test_group_chat.py::test_user_message_with_mention` - integration test for flow
- None - existing test infrastructure (pytest) is available

---

## Sources

### Primary (HIGH confidence)
- Python `re` module official documentation - regex patterns
- Existing codebase: `group_chat_service.py` - integration points

### Secondary (MEDIUM confidence)
- WebSearch (failed during research, using established patterns)

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - using built-in Python `re`, no new dependencies
- Architecture: HIGH - clear integration point in existing code
- Pitfalls: HIGH - well-understood edge cases for regex matching

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (30 days - stable domain)
