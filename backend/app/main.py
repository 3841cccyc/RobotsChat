from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import bots, chat, group_chat, documents, users, groups
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    print("数据库初始化完成")
    yield
    # 关闭时清理资源
    print("应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="机器人对话系统 API",
    description="多机器人对话系统，支持独立人格、长文档理解、群聊功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(bots.router)
app.include_router(chat.router)
app.include_router(group_chat.router)
app.include_router(documents.router)
app.include_router(users.router)
app.include_router(groups.router)


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "欢迎使用机器人对话系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    import sys

    # 确保 print 输出立即刷新
    sys.stdout.reconfigure(line_buffering=True)

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
        access_log=True
    )
