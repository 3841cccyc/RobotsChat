# Research Summary: 流式输出去重技术

**Domain:** LLM 流式输出处理
**Researched:** 2026-03-14
**Overall confidence:** HIGH

## Executive Summary

本项目当前采用"先获取完整响应再模拟流式输出"的后处理模式，去重逻辑在流式输出前执行。这种方式实现简单，但用户需要等待 LLM 完整响应才能开始接收输出。真正的实时流式去重需要引入滑动窗口检测、缓冲区批量处理等技术。

## Key Findings

**Stack:** FastAPI + MiniMax LLM + 自研去重器
**Architecture:** 后处理去重 → 实时流式去重 → 混合策略(推荐)
**Critical pitfall:** 当前模拟流式无法利用 LLM 原生流式的首 token 快速响应优势

## Implications for Roadmap

基于研究，建议的技术演进路线:

1. **Phase 1 (保持现状)** - 优化后处理去重
   - 调整 `_deduplicate_text` 正则参数
   - 改进模拟流式的 chunk_size 和延迟

2. **Phase 2 (流式改造)** - 实现真实流式去重
   - 切换到 MiniMax 原生流式 API
   - 实现 StreamingDeduplicator
   - 优先级: 中等

3. **Phase 3 (增强功能)** - 消息截断
   - 实现 MessageTruncator
   - 处理超长响应自动拆分
   - 优先级: 低

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 基于 FastAPI 原生能力和项目现有代码 |
| Streaming | HIGH | asyncio + AsyncGenerator 模式成熟 |
| Deduplication | HIGH | 项目已有实现，正则方案可靠 |
| Truncation | MEDIUM | 需要根据实际消息平台限制调整 |

## Gaps to Address

- MiniMax 流式 API 具体参数需要验证
- 真实流式下的去重效果需要实测
- 前端 SSE 接收和渲染性能测试
