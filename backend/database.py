# backend/database.py
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 获取项目根目录
project_root = Path(__file__).parent.parent

# 数据库文件路径 - 使用项目根目录下的news.db
db_path = project_root / "news.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# 创建数据库连接（固定写法，不用改）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 专用
)

# 创建会话（用来操作数据库）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
