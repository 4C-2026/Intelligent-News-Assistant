# backend/services/news_service.py
from sqlalchemy.orm import Session
from models.article import Article
from typing import List, Dict, Any, Optional


class NewsService:
    @staticmethod
    def get_news_list(db: Session, page: int = 1, size: int = 10) -> Dict[str, Any]:
        """获取新闻列表，返回分页数据和总数"""
        skip = (page - 1) * size
        # 按发布时间倒序排列，最新的在前面。如果发布时间为空，则按照数据库ID倒序（最新入库的）
        articles = db.query(Article).order_by(
            Article.published_at.desc().nullslast(),
            Article.id.desc()
        ).offset(skip).limit(size).all()
        total = db.query(Article).count()

        items = [
            {
                "id": a.id,
                "title": a.title,
                "summary": a.summary,
                "tags": a.tags,
                "cover_image": getattr(a, "cover_image", None),
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
            "cover_image": getattr(article, "cover_image", None),
            "published_at": article.published_at.isoformat() if article.published_at else None,
        }
