# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "sqlite:///./test.db"
    # JWT
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    zhipu_api_key: str          # 对应 ZHIPU_API_KEY
    cors_origins: str           # 对应 CORS_ORIGINS
    chroma_persist_dir: str = "./chroma_data"  # 对应 CHROMA_PERSIST_DIR，设置默认值

    class Config:
        env_file = ".env"          # 从 .env 文件读取
        env_file_encoding = "utf-8"

settings = Settings()
