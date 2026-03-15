---
phase: "02-short-message"
plan: "01"
subsystem: "group_chat_service"
tags: [short-message, 20-char, streaming]
dependency_graph:
  requires: []
  provides:
    - "_split_into_short_messages with max_length=20"
    - "event_generator with 1-second delay"
  affects:
    - "group_chat router"
    - "auto_chat_rounds"
tech_stack:
  added: []
  patterns:
    - "断点优先级: 句号/问号/感叹号 > 逗号/顿号 > 强制截断"
    - "1秒固定发送间隔"
key_files:
  created: []
  modified:
    - "backend/app/services/group_chat_service.py"
    - "backend/app/routers/group_chat.py"
decisions:
  - "采用20字短消息阈值（用户明确需求）"
  - "断点优先级: 句号/问号/感叹号 > 逗号 > 强制截断"
  - "1秒发送间隔"
metrics:
  duration: "2 min"
  completed_date: "2026-03-15"
---

# Phase 2 Plan 1: 20字短消息拆分与连续输出效果 Summary

## Objective
实现20字短消息拆分与连续输出效果 - 将机器人长输出拆分为≤20字/条的短消息，在自然断点拆分，并间隔1秒依次发送。

## One-Liner
实现了20字短消息拆分与1秒延迟发送机制

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | 修改 _split_into_short_messages 为20字限制并优化断点优先级 | f59f375 | group_chat_service.py |
| 2 | 在 router event_generator 中添加1秒延迟发送机制 | d838fa9 | group_chat.py |
| 3 | 更新 auto_chat_rounds 使用新的20字拆分 | f59f375 | group_chat_service.py |

## Key Changes

### 1. _split_into_short_messages 方法优化
- **max_length**: 从80改为20
- **断点优先级**:
  - 第一优先级: 句号、问号、感叹号（。！？）
  - 第二优先级: 逗号、顿号（，、）
  - 第三优先级: 强制截断
- **拆分逻辑**: 在20字内优先找句号/问号/感叹号 → 其次找逗号 → 最后强制截断

### 2. event_generator 延迟发送
- 在 `start_group_chat_stream` 和 `add_group_message_stream` 两个端点添加1秒延迟
- 发送拆分信号 `message_split` 后，逐条发送短消息
- 每条消息间隔1秒发送

### 3. auto_chat_rounds 同步更新
- 将 `max_length=80` 改为 `max_length=20`
- 延迟简化为固定1秒

## Verification

- [x] _split_into_short_messages 方法 max_length=20
- [x] 断点优先级: 句号/问号/感叹号 > 逗号 > 强制截断
- [x] event_generator 中有 await asyncio.sleep(1.0)
- [x] auto_chat_rounds 使用 max_length=20

## Success Criteria

- [x] 每条短消息≤20个汉字
- [x] 拆分优先在句号、问号、感叹号处
- [x] 多条消息间隔1秒发送
- [x] 用户在群聊中看到连续对话效果

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

All modifications verified:
- backend/app/services/group_chat_service.py: max_length=20 found at lines 246 and 698
- backend/app/routers/group_chat.py: await asyncio.sleep(1.0) found at lines 224 and 356
