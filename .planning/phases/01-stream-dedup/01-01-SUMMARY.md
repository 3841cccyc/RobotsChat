---
phase: "01-stream-dedup"
plan: "01"
subsystem: "backend-streaming"
tags: [dedup, streaming, n-gram, real-time]
dependency_graph:
  requires: []
  provides:
    - "streaming_dedup.NGramDetector"
    - "streaming_dedup.BufferedDeduplicator"
    - "streaming_dedup.HistoryChecker"
    - "llm_service.chat_stream use_stream_dedup"
  affects:
    - "llm_service"
    - "group_chat_service"
tech_stack:
  added:
    - "n-gram character-level detection"
    - "deque-based sliding window"
    - "async buffer flush"
  patterns:
    - "real-time chunk processing"
    - "history-based filtering"
key_files:
  created:
    - "backend/app/services/streaming_dedup.py"
  modified:
    - "backend/app/services/llm_service.py"
    - "backend/app/services/group_chat_service.py"
decisions:
  - "采用 n=4 的字符级 n-gram 检测"
  - "使用缓冲区批量去重方案而非逐块检测"
  - "保留原有的 _deduplicate_text 作为后处理 fallback"
metrics:
  duration: "2 minutes"
  completed_date: "2026-03-15"
---

# Phase 1 Plan 1: 流式输出去重核心 Summary

实现实时流式输出中的重复内容检测与过滤，确保用户看不到重复消息。

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create streaming_dedup.py module | 767f3a6 | backend/app/services/streaming_dedup.py |
| 2 | Integrate dedup into llm_service | 66b4013 | backend/app/services/llm_service.py |
| 3 | Integrate history into group_chat_service | 34d8951 | backend/app/services/group_chat_service.py |

## What Was Built

1. **streaming_dedup.py** - 核心去重模块包含三个类:
   - `NGramDetector`: 使用 n=4 字符级 n-gram 检测连续重复
   - `BufferedDeduplicator`: 缓冲区批量去重，支持异步 flush
   - `HistoryChecker`: 历史消息去重，使用 Jaccard 相似度检测

2. **llm_service.py** - chat_stream 方法增强:
   - 新增 `use_stream_dedup` 参数（默认为 True）
   - 每个 chunk 通过 BufferedDeduplicator 处理
   - 流结束后 flush 剩余内容

3. **group_chat_service.py** - 历史消息集成:
   - HistoryChecker 追踪历史消息
   - 使用 use_stream_dedup=True 启用实时去重
   - 内联去重使用 ngram_detector.get_unique_tail

## Deviations from Plan

None - plan executed exactly as written.

## Verification

All imports verified:
- `python -c "from backend.app.services.streaming_dedup import NGramDetector, BufferedDeduplicator, HistoryChecker; print('Import OK')"`
- `python -c "from backend.app.services.llm_service import LLMService; print('Import OK')"`
- `python -c "from backend.app.services.group_chat_service import GroupChatService; print('Import OK')"`

## Self-Check

- [x] streaming_dedup.py created with all three classes
- [x] llm_service.py chat_stream has use_stream_dedup parameter
- [x] group_chat_service.py integrates HistoryChecker
- [x] All three commits exist (767f3a6, 66b4013, 34d8951)
- [x] Requirements DEDUP-01, DEDUP-02, DEDUP-03 addressed

## Self-Check: PASSED
