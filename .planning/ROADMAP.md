# Roadmap: 机器人对话系统优化

**Project:** 机器人对话系统优化
**Core Value:** 机器人能够在群聊中自主、简洁、无重复地进行连续对话，用户可随时加入讨论。
**Created:** 2026-03-14
**Granularity:** fine

## Phases

- [x] **Phase 1: 流式去重核心** - 实现实时流式输出中的重复内容检测与过滤 (completed 2026-03-14)
- [x] **Phase 2: 短消息输出** - 实现≤20字短消息的截断与连续输出 (completed 2026-03-15)
- [x] **Phase 3: 用户互动机制** - 实现@提及和用户触发响应 (completed 2026-03-15)

---

## Phase Details

### Phase 1: 流式去重核心

**Goal:** 实时检测流式输出中的重复内容，在发送到前端前过滤，确保用户看不到重复消息

**Depends on:** 无

**Requirements:**
- DEDUP-01: 实时检测流式输出中的重复内容，在发送到前端前过滤
- DEDUP-02: 基于 n-gram 的去重算法，过滤连续重复短语
- DEDUP-03: 与历史消息比对，防止重复已发送内容

**Success Criteria** (what must be TRUE):
1. 用户在群聊中观看机器人对话时，看不到连续重复的短语（如"你好你好"）
2. 机器人连续输出的内容中，不会出现已经发送过的历史消息片段
3. 去重操作在流式输出过程中实时执行，不影响输出延迟
4. 用户可以正常发送消息，机器人响应中无明显重复内容

**Plans:** 1/1 plans complete

- [x] 01-PLAN.md — 创建streaming_dedup模块，集成到llm_service和group_chat_service

---

### Phase 2: 短消息输出

**Goal:** 将长输出截断为≤20字/条的短消息，在合理断点拆分，实现连续输出效果

**Depends on:** Phase 1

**Requirements:**
- SHORT-01: 截断长输出为 ≤20字/条 的短消息
- SHORT-02: 在合理断点（句号、逗号、问号）拆分消息
- SHORT-03: 实现连续输出效果，每条短消息间隔发送

**Success Criteria** (what must be TRUE):
1. 用户看到机器人输出时，每条消息≤20个汉字
2. 消息拆分点在句号、逗号、问号等自然断点，不会截断单词或成语
3. 多条短消息依次发送，间隔时间自然（不堆积也不错慢）
4. 用户在群聊中看到的是连续对话效果，而非一次性长文本

**Plans:** 1/1 plans complete

- [x] 02-PLAN.md — 修改 _split_into_short_messages 为20字限制，优化断点优先级，添加1秒延迟发送机制 (complete)

---

### Phase 3: 用户互动机制

**Goal:** 用户可以通过@提及机器人或@所有人来参与对话，触发机器人响应

**Depends on:** Phase 2

**Requirements:**
- USER-01: 用户@提及机制，支持@特定机器人或@所有人
- USER-02: 用户消息触发机器人响应流程

**Success Criteria** (what must be TRUE):
1. 用户在群聊中输入"@机器人名"时，机器人能够识别并响应
2. 用户输入"@所有人"时，所有机器人都能识别
3. 用户发送消息后，机器人自动参与对话（当被@时）
4. 用户可以随时加入机器人讨论话题，无需等待

**Plans:** 1/1 plans complete

- [x] 03-01-PLAN.md — 实现@mention解析函数和响应筛选 (complete)

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 流式去重核心 | 1/1 | Complete    | 2026-03-14 |
| 2. 短消息输出 | 1/1 | Complete    | 2026-03-15 |
| 3. 用户互动机制 | 1/1 | Complete    | 2026-03-15 |

---

## Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| DEDUP-01 | Phase 1 | Complete |
| DEDUP-02 | Phase 1 | Complete |
| DEDUP-03 | Phase 1 | Complete |
| SHORT-01 | Phase 2 | Complete |
| SHORT-02 | Phase 2 | Complete |
| SHORT-03 | Phase 2 | Complete |
| USER-01 | Phase 3 | Complete |
| USER-02 | Phase 3 | Complete |

**v1 Coverage:** 8/8 (100%) ✓

---

*Last updated: 2026-03-15*
