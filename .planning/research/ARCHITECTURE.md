# 实时聊天系统架构研究

**项目:** 机器人对话系统（多机器人群聊平台）
**研究日期:** 2025-03-14
**研究重点:** SSE、FastAPI 异步架构、消息队列与流式处理

## 1. SSE (Server-Sent Events) 在实时聊天中的使用

### 1.1 当前项目实现分析

项目已实现基于 SSE 的流式响应，核心实现位于 `backend/app/routers/group_chat.py`：

```python
# 流式响应端点示例
@router.post("/start-stream")
async def start_group_chat_stream(request: GroupChatStartRequest, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        # ... 生成事件 ...
        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 1.2 SSE 架构模式

| 模式 | 描述 | 适用场景 | 当前项目状态 |
|------|------|----------|--------------|
| **直接 SSE** | 请求-响应直接返回 SSE 流 | 单用户实时聊天 | 已实现 |
| **轮询 + SSE** | HTTP 轮询获取状态，SSE 接收推送 | 需要状态管理的复杂场景 | 未实现 |
| **SSE + Redis** | SSE 接收消息，Redis 分发 | 多实例部署 | 可扩展方向 |
| **WebSocket + SSE 混合** | WebSocket 双向，SSE 单向推送 | 需要双向交互的场景 | 未实现 |

### 1.3 SSE 最佳实践

**推荐实现模式：**

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
import json

async def sse_event_generator(queue: asyncio.Queue):
    """标准的 SSE 事件生成器"""
    try:
        while True:
            # 等待新消息（带超时以保持连接活跃）
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"data: {json.dumps(message)}\n\n"
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                yield f": heartbeat\n\n"

    except asyncio.CancelledError:
        # 客户端断开连接
        print("Client disconnected")
    finally:
        # 清理资源
        await cleanup()
```

**SSE 事件格式规范：**

| 事件类型 | 格式 | 说明 |
|----------|------|------|
| 消息 | `data: {"type": "message", "content": "..."}` | 聊天消息 |
| 开始 | `data: {"type": "bot_start", "bot_name": "..."}` | 机器人开始回复 |
| 完成 | `data: {"type": "bot_done", "bot_name": "..."}` | 机器人完成回复 |
| 错误 | `data: {"error": "..."}` | 错误信息 |
| 心跳 | `: heartbeat` | 保持连接 |

### 1.4 SSE 优势与局限

**优势：**
- 简单易用，基于标准 HTTP
- 自动重连机制
- 无需前端额外库（原生 EventSource API）
- 适合服务端推送场景

**局限：**
- 单向通信（服务端 -> 客户端）
- 浏览器并发连接数限制（6个/域名）
- 无二进制数据支持
- 不适合需要高频率双向通信的场景

---

## 2. FastAPI 异步聊天系统架构

### 2.1 当前项目架构

```
┌─────────────────────────────────────────────────────────────┐
│                         FastAPI App                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌─────────────────┐                   │
│  │   Routers    │ -> │    Services     │                  │
│  │ group_chat.py │    │ group_chat_     │                  │
│  │    chat.py    │    │ service.py      │                  │
│  └──────────────┘    │ llm_service.py   │                  │
│                      └─────────────────┘                   │
│                              │                              │
│                      ┌───────┴───────┐                    │
│                      ▼               ▼                     │
│              ┌──────────────┐ ┌──────────────┐            │
│              │  LLM API      │ │   Database   │            │
│              │ (Anthropic)   │ │  (SQLAlchemy) │            │
│              └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 异步架构模式

| 模式 | 描述 | 复杂度 | 推荐程度 |
|------|------|--------|----------|
| **同步调用** | 顺序等待 LLM 响应 | 低 | 不推荐 |
| **异步流式** | 异步调用 LLM，流式返回 | 中 | 当前使用 |
| **后台任务** | 消息处理放入后台任务 | 中 | 推荐扩展 |
| **消息队列** | 引入 MQ 解耦 | 高 | 规模化推荐 |

### 2.3 推荐架构改进

**分层架构：**

```python
# 1. 路由层 - 请求验证和响应格式化
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # 仅做请求验证，不包含业务逻辑
    validated = await validate_request(request)
    return await handle_chat(validated)

# 2. 服务层 - 业务逻辑
class ChatService:
    async def process_message(self, request):
        # 业务逻辑处理
        await self.save_to_database()
        await self.call_llm_stream()

# 3. 消息队列层 - 扩展解耦（未来方向）
class MessageQueueService:
    async def publish(self, channel: str, message: dict):
        await redis.publish(channel, json.dumps(message))
```

### 2.4 并发控制

项目当前使用内存锁进行并发控制：

```python
class GroupChatService:
    def __init__(self):
        self._active_loops: Dict[int, str] = {}  # 内存锁

    def _acquire_lock(self, conversation_id: int) -> str:
        if conversation_id in self._active_loops:
            return None  # 已被占用
        loop_id = str(uuid.uuid4())
        self._active_loops[conversation_id] = loop_id
        return loop_id
```

**扩展方案：**

| 方案 | 适用场景 | 复杂度 |
|------|----------|--------|
| 内存锁 | 单实例部署 | 低 |
| Redis 分布式锁 | 多实例部署 | 中 |
| 数据库行锁 | 持久化需求 | 中 |
| Redis Pub/Sub | 跨实例消息同步 | 高 |

---

## 3. 消息队列和流式处理架构

### 3.1 当前项目的流式处理流程

```
用户请求
    │
    ▼
┌─────────────────┐
│  路由层         │  接收请求，创建会话
│ group_chat.py  │
└────────┬────────
         │
         ▼
┌─────────────────┐
│  服务层         │  获取机器人，构建上下文
│ group_chat_    │
│ service.py     │
└────────┬────────
         │
         ▼
┌─────────────────┐
│  LLM 服务       │  流式调用 LLM API
│ llm_service.py  │
└────────┬────────
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ SSE   │ │ DB    │
│ 推送  │ │ 存储  │
└───────┘ └───────┘
```

### 3.2 消息队列使用场景

**当前项目的痛点：**
1. LLM 调用耗时高，阻塞请求线程
2. 多实例部署时无法共享状态
3. 无法削峰填谷，高并发时容易崩溃

**消息队列解决方案：**

| 场景 | 解决方案 | 架构变化 |
|------|----------|----------|
| LLM 调用异步化 | Redis Queue / Celery | 请求 -> 队列 -> Worker -> SSE |
| 多实例消息同步 | Redis Pub/Sub | 实例间消息广播 |
| 消息持久化 | RabbitMQ / Kafka | 防止消息丢失 |
| 限流削峰 | 消息队列缓冲 | 保护后端 LLM API |

### 3.3 推荐架构：Redis + Celery

```
┌──────────────────────────────────────────────────────────────────┐
│                         Client (Frontend)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ SSE / WebSocket
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  API Routes                                            │    │
│  │  - /chat/start        -> 创建任务，返回 task_id        │    │
│  │  - /chat/stream/{id} -> SSE 流式获取结果              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              ▼               ▼               ▼                  │
│     ┌────────────┐   ┌────────────┐   ┌────────────┐          │
│     │  Task Queue│   │   Redis    │   │  Database  │          │
│     │  (Celery)  │   │  Pub/Sub   │   │  (SQLite)  │          │
│     └─────┬──────┘   └────────────┘   └────────────┘          │
│           │                                                    │
│           ▼                                                    │
│     ┌────────────┐                                             │
│     │   Workers │  LLM 调用、消息处理                          │
│     │ (Celery)  │                                             │
│     └────────────┘                                             │
└──────────────────────────────────────────────────────────────────┘
```

### 3.4 消息队列实现示例

**Redis Queue 实现：**

```python
import asyncio
import aioredis
import json
from typing import AsyncGenerator

class MessageQueueService:
    def __init__(self):
        self.redis: aioredis.Redis = None

    async def connect(self):
        self.redis = await aioredis.create_redis_pool('redis://localhost')

    async def publish(self, channel: str, message: dict):
        """发布消息到频道"""
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        """订阅频道"""
        channel = self.redis.channel(channel)
        async for message in channel.iter():
            yield json.loads(message)

# Celery 任务定义
from celery import Celery

celery_app = Celery('chat_tasks')

@celery_app.task
def process_llm_message(bot_id: int, messages: list, conversation_id: int):
    """后台 LLM 处理任务"""
    result = call_llm_api(bot_id, messages)
    # 将结果发布到 SSE 频道
    redis_client.publish(f"chat:{conversation_id}", {
        "type": "result",
        "bot_id": bot_id,
        "content": result
    })
    return result
```

**FastAPI + Celery 集成：**

```python
from fastapi import FastAPI, BackgroundTasks
from celery.result import AsyncResult

@router.post("/chat/start")
async def start_chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """启动聊天，返回 task_id"""
    task = celery_app.send_task('process_llm_message', args=[...])
    return {"task_id": task.id}

@router.get("/chat/stream/{task_id}")
async def stream_chat(task_id: str):
    """通过 SSE 流式获取任务结果"""
    async def event_generator():
        task = AsyncResult(task_id)

        while not task.ready():
            await asyncio.sleep(0.5)
            yield f"data: {json.dumps({'status': 'processing'})}\n\n"

        result = task.result
        yield f"data: {json.dumps({'status': 'done', 'result': result})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 3.5 流式处理优化

**当前项目问题分析：**

| 问题 | 当前状态 | 优化建议 |
|------|----------|----------|
| LLM 调用阻塞 | 同步等待后模拟流式 | 真正的流式调用或后台任务 |
| 无消息持久化 | 仅存数据库 | 引入消息队列保证可靠性 |
| 单实例限制 | 内存锁 | Redis 分布式锁 |
| 无重试机制 | 无 | Celery 重试策略 |

**LLM 流式调用优化：**

```python
# 当前：先获取完整响应，再模拟流式（延迟高）
async def chat_stream(self, messages, system_prompt):
    full_response = await self.get_full_response(messages)  # 等待完整响应
    # 模拟流式输出
    for chunk in split_into_chunks(full_response):
        yield chunk

# 优化：真正的流式响应（推荐）
async def chat_stream_true(self, messages, system_prompt):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            self.api_url,
            json={"stream": True, ...}
        ) as resp:
            async for line in resp.content:
                if line.startswith(b"data:"):
                    yield line.decode().replace("data:", "").strip()
```

---

## 4. 架构决策建议

### 4.1 近期改进（1-2 个月）

| 改进项 | 优先级 | 预期收益 |
|--------|--------|----------|
| 真正的 LLM 流式调用 | 高 | 减少首字延迟 2-3 秒 |
| SSE 连接健康检查 | 中 | 提高连接稳定性 |
| Redis 分布式锁 | 中 | 支持多实例部署 |
| 请求去重/幂等 | 中 | 防止重复提交 |

### 4.2 中期改进（3-6 个月）

| 改进项 | 优先级 | 预期收益 |
|--------|--------|----------|
| 引入 Celery 任务队列 | 高 | 解耦 LLM 调用，提高吞吐量 |
| 消息持久化 | 中 | 防止高并发时消息丢失 |
| WebSocket 支持 | 中 | 支持更复杂的双向交互 |

### 4.3 架构演进路线

```
Phase 1: 基础功能 (当前)
  └── 同步 LLM 调用 + SSE 流式返回

Phase 2: 性能优化
  └── 真正的流式 LLM 调用
  └── Redis 分布式锁

Phase 3: 规模化
  └── Celery 任务队列
  └── Redis Pub/Sub 消息分发

Phase 4: 高可用
  └── 多 Worker 部署
  └── 消息持久化 (Kafka)
  └── 限流和熔断
```

---

## 5. 总结

### 5.1 项目架构评估

| 维度 | 当前状态 | 评分 | 说明 |
|------|----------|------|------|
| 功能完整性 | 中 | 3/5 | 基础聊天功能完整 |
| 性能 | 中 | 3/5 | LLM 调用有延迟 |
| 可扩展性 | 低 | 2/5 | 单实例、无队列 |
| 可靠性 | 中 | 3/5 | 基础错误处理 |
| 实时性 | 高 | 4/5 | SSE 实时推送 |

### 5.2 关键发现

1. **SSE 使用正确**：项目已正确实现 SSE 流式响应，事件格式规范
2. **异步架构基础良好**：使用 FastAPI + AsyncSession，符合现代异步开发模式
3. **缺少消息队列**：LLM 调用与请求处理紧耦合，限制吞吐量
4. **无状态设计缺失**：使用内存锁，无法支持多实例部署

### 5.3 推荐行动

**立即行动：**
- 将 LLM 调用改为真正的流式响应
- 添加 SSE 心跳机制防止连接断开

**短期行动：**
- 引入 Redis 用于分布式锁和消息发布/订阅
- 添加请求幂等性保证

**中期行动：**
- 引入 Celery 实现任务队列
- 支持多 Worker 部署

---

## 6. 参考资料

### 官方文档
- [FastAPI Streaming Responses](https://fastapi.tiangolo.com/advanced/custom-response/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Celery Documentation](https://docs.celeryproject.org/)

### 技术博客
- [Real-time Chat with FastAPI and SSE](https://medium.com/@stephenjun08/real-time-chat-with-fastapi-and-sse)
- [FastAPI SSE Best Practices](https://betterprogramming.pub/fastapi-server-sent-events-ef580d6d5c6a)

### 相关项目
- [FastAPI Real-time Chat Example](https://github.com/sanguyeenx96/FastAPI_RealTime_Chat)
- [Celery FastAPI Integration](https://github.com/marksteele/netcode-io-fastapi-celery)
