# 机器人对话系统优化

## What This Is

一个基于 FastAPI + React 的多机器人对话 web 应用，支持机器人之间自动讨论、用户加入群聊、解决群聊中机器人重复输出问题，并实现短消息连续输出（≤20字/条）。

## Core Value

机器人能够在群聊中自主、简洁、无重复地进行连续对话，用户可随时加入讨论。

## Requirements

### Validated

- ✓ 机器人创建和管理 — 现有
- ✓ 1对1对话 — 现有
- ✓ 群聊功能（多机器人自动讨论）— 现有
- ✓ 用户加入群聊发送消息 — 现有
- ✓ 消息历史存储（SQLite）— 现有
- ✓ 流式输出 — 现有
- ✓ 流式输出实时去重 (n-gram) — v1.0
- ✓ 短消息截断输出（≤20字/条）— v1.0
- ✓ 用户@机器人机制 — v1.0

### Active

(TBD - define new requirements for next milestone)

### Out of Scope

- 语音/视频消息 — 非核心功能
- 文件上传分享 — 非核心功能

## Context

**技术栈：**
- 后端：FastAPI + SQLAlchemy + aiosqlite
- 前端：React + TypeScript + Vite + TailwindCSS
- LLM：MiniMax API（兼容 Anthropic SDK）

**现有架构：**
- 双聊天系统：1对1聊天 + 群聊（完全隔离）
- 已有去重逻辑（`_deduplicate_response`）但效果不佳
- 已有消息拆分（`_split_into_short_messages`，80字阈值）

**问题分析：**
- 当前去重是事后处理，流式输出时已产生重复
- 80字阈值太高，用户期望20字短消息
- 需要实时监控输出流，在生成过程中去重

## Constraints

- **LLM API**：依赖 MiniMax API，需保持兼容
- **数据库**：SQLite，生产环境可能需要迁移
- **实时性**：流式输出需低延迟

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 20字短消息 | 用户明确需求，类似微信/QQ风格 | ✓ 成功实现 |
| 流式实时去重 | 事后去重无法解决流式重复问题 | ✓ n-gram 4gram 有效 |
| @mention 模糊匹配 | 支持@机器人名或@all | ✓ 不区分大小写 |

## Current State

**v1.0 MVP 已完成 (2026-03-15)**
- 3 phases, 3 plans, 所有 8 个需求已验证
- 核心功能：流式去重、短消息输出、@mention用户互动

**下一步：** 运行 `/gsd:new-milestone` 开始规划新功能

---
*Last updated: 2026-03-15 after v1.0 milestone*
