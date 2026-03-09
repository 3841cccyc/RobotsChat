from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MiniMax API 配置
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimaxi.com/anthropic"
    minimax_model: str = "MiniMax-M2.5"

    # Embedding 配置
    openai_api_key: str = ""  # 用于向量检索（可选）
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./chatbot.db"
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
