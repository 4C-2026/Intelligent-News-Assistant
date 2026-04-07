# user_profile.py - 用户画像服务
from typing import List, Optional
from sqlalchemy.orm import Session
from models import Interaction, Article


def get_user_liked_articles(db: Session, user_id: int) -> List[int]:
    """获取用户点赞过的新闻ID列表"""
    likes = db.query(Interaction).filter(
        Interaction.user_id == user_id,
        Interaction.action_type == "like"
    ).all()
    
    return [like.article_id for like in likes]


def get_user_read_articles(db: Session, user_id: int) -> List[int]:
    """获取用户阅读过的新闻ID列表"""
    reads = db.query(Interaction).filter(
        Interaction.user_id == user_id,
        Interaction.action_type == "read"
    ).all()
    
    return [read.article_id for read in reads]


def get_user_interactions(db: Session, user_id: int) -> dict:
    """获取用户所有互动记录"""
    liked_ids = get_user_liked_articles(db, user_id)
    read_ids = get_user_read_articles(db, user_id)
    
    return {
        "user_id": user_id,
        "liked_articles": liked_ids,
        "read_articles": read_ids,
        "liked_count": len(liked_ids),
        "read_count": len(read_ids)
    }


def get_user_liked_article_objects(db: Session, user_id: int) -> List[Article]:
    """获取用户点赞过的新闻对象列表（用于成员B的向量化服务）"""
    liked_ids = get_user_liked_articles(db, user_id)
    if not liked_ids:
        return []
    return db.query(Article).filter(Article.id.in_(liked_ids)).all()


def get_user_read_article_objects(db: Session, user_id: int) -> List[Article]:
    """获取用户阅读过的新闻对象列表（用于成员B的向量化服务）"""
    read_ids = get_user_read_articles(db, user_id)
    if not read_ids:
        return []
    return db.query(Article).filter(Article.id.in_(read_ids)).all()


def calculate_user_preference(db: Session, user_id: int) -> Optional[dict]:
    """
    计算用户偏好向量
    注意：需要与成员B对接，调用他的向量化服务
    """
    # 获取用户互动过的新闻
    liked_articles = get_user_liked_article_objects(db, user_id)
    read_articles = get_user_read_article_objects(db, user_id)
    
    # 合并并去重
    all_articles = list({article.id: article for article in liked_articles + read_articles}.values())
    
    if not all_articles:
        return None
    
    # TODO: 对接成员B的向量化服务
    # from services.embedding_service import get_embedding
    # vectors = [get_embedding(article.content) for article in all_articles]
    # preference_vector = sum(vectors) / len(vectors)
    
    return {
        "user_id": user_id,
        "article_count": len(all_articles),
        "liked_count": len(liked_articles),
        "read_count": len(read_articles),
        "article_ids": [article.id for article in all_articles]
    }
