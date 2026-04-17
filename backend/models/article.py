from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .base import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    tags = Column(String(200))  # 逗号分隔的标签
    source_url = Column(String(500))  # 原文链接 
    cover_image = Column(String(500), nullable=True) # 封面图链接
    published_at = Column(DateTime)  # 发布时间 
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
    