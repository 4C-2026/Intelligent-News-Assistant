# backend/services/news_service.py
from sqlalchemy.orm import Session
from models.article import Article
from typing import List, Dict, Any, Optional


class NewsService:
    @staticmethod
    def get_news_list(db: Session, page: int = 1, size: int = 10) -> Dict[str, Any]:
        """获取新闻列表，返回分页数据和总数"""
        skip = (page - 1) * size
        articles = db.query(Article).offset(skip).limit(size).all()
        total = db.query(Article).count()

        items = [
            {
                "id": a.id,
                "title": a.title,
                "summary": a.summary,
                "tags": a.tags,
                "published_at": a.published_at.isoformat() if a.published_at else None,
            }
            for a in articles
        ]
        return {
            "data": items,
            "total": total,
            "page": page,
            "size": size
        }

    @staticmethod
    def get_news_detail(db: Session, news_id: int) -> Optional[Dict[str, Any]]:
        """获取新闻详情，返回字典或 None"""
        article = db.query(Article).filter(Article.id == news_id).first()
        if not article:
            return None

        return {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "tags": article.tags,
            "source_url": article.source_url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
        }
