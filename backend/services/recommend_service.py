# backend/services/recommend_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.article import Article
from models.interaction import Interaction
from services.embedding_service import get_embedding
from services.vector_store import search_by_vector
import numpy as np
from datetime import datetime, timedelta


def get_user_liked_articles(db: Session, user_id: int) -> List[int]:
    """
    获取用户点赞的所有新闻ID列表

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        List[int]: 用户点赞的新闻ID列表
    """
    interactions = db.query(Interaction.article_id).filter(
        Interaction.user_id == user_id,
        Interaction.action_type == "like"
    ).all()

    return [article_id for article_id, in interactions]


def get_popular_articles(db: Session, limit: int = 10, days: int = 7) -> List[int]:
    """
    获取最近最受欢迎的新闻ID列表（基于点赞数量排序）
    "最近"是指新闻的发布时间（published_at）在指定天数内

    Args:
        db: 数据库会话
        limit: 返回数量
        days: 最近多少天内

    Returns:
        List[int]: 热门新闻ID列表
    """
    # 计算时间范围：只统计最近N天内发布的新闻
    time_threshold = datetime.now() - timedelta(days=days)

    # 统计最近N天内发布的新闻的点赞数量
    from sqlalchemy import func

    # 先获取最近N天内发布的新闻ID
    recent_article_ids = db.query(Article.id).filter(
        Article.published_at >= time_threshold
    ).all()

    recent_article_ids = [aid for aid, in recent_article_ids]

    if not recent_article_ids:
        # 如果最近没有新闻，返回空列表
        return []

    # 统计这些新闻的点赞数量
    popular_query = db.query(
        Interaction.article_id,
        func.count(Interaction.id).label('like_count')
    ).filter(
        Interaction.action_type == 'like',
        Interaction.article_id.in_(recent_article_ids)
    ).group_by(
        Interaction.article_id
    ).order_by(
        func.count(Interaction.id).desc()
    ).limit(limit)

    # 获取新闻ID列表
    popular_ids = [article_id for article_id, _ in popular_query.all()]

    return popular_ids


def calculate_average_vector(db: Session, article_ids: List[int]) -> Optional[List[float]]:
    """
    计算多篇新闻向量的平均值

    Args:
        db: 数据库会话
        article_ids: 新闻ID列表

    Returns:
        List[float] or None: 平均向量，如果计算失败返回None
    """
    if not article_ids:
        return None

    try:
        # 从数据库获取新闻内容
        articles = db.query(Article).filter(Article.id.in_(article_ids)).all()

        if not articles:
            return None

        # 获取每篇新闻的向量
        embeddings = []
        for article in articles:
            try:
                embedding = get_embedding(article.content)
                embeddings.append(embedding)
            except Exception as e:
                print(f"⚠️ 新闻 {article.id} 向量化失败: {e}")
                continue

        if not embeddings:
            return None

        # 计算平均向量
        average_embedding = np.mean(embeddings, axis=0).tolist()

        return average_embedding

    except Exception as e:
        print(f"❌ 计算平均向量失败: {e}")
        return None


def get_personalized_recommendations(
    db: Session,
    user_id: int,
    limit: int = 10,
    exclude_article_ids: Optional[List[int]] = None
) -> List[int]:
    """
    基于用户点赞历史生成个性化推荐（使用向量相似度）

    Args:
        db: 数据库会话
        user_id: 用户ID
        limit: 返回数量
        exclude_article_ids: 需要排除的新闻ID列表（如用户已点赞的新闻）

    Returns:
        List[int]: 推荐新闻ID列表
    """
    exclude_article_ids = exclude_article_ids or []

    # 1. 获取用户点赞的新闻ID
    liked_article_ids = get_user_liked_articles(db, user_id)

    if not liked_article_ids:
        # 如果用户没有点赞记录，返回空列表
        return []

    # 2. 计算用户点赞新闻的平均向量
    average_vector = calculate_average_vector(db, liked_article_ids)

    if not average_vector:
        # 如果向量化失败，返回空列表
        return []

    # 3. 使用平均向量在向量库中搜索相似新闻
    similar_article_ids = search_by_vector(average_vector, n_results=limit * 2)

    if not similar_article_ids:
        return []

    # 4. 过滤掉用户已点赞的新闻
    recommended_ids = [
        aid for aid in similar_article_ids
        if aid not in liked_article_ids and aid not in exclude_article_ids
    ]

    # 5. 从数据库获取这些新闻，按发布时间排序（只返回最近的）
    recommended_articles = db.query(Article).filter(
        Article.id.in_(recommended_ids)
    ).order_by(
        Article.published_at.desc()
    ).limit(limit).all()

    final_ids = [article.id for article in recommended_articles]

    return final_ids


def get_recommendations(
    db: Session,
    user_id: int,
    limit: int = 10
) -> Dict[str, Any]:
    """
    智能推荐：根据用户点赞历史返回推荐文章

    逻辑：
    1. 如果用户没有点赞记录 -> 返回最近的热门新闻
    2. 如果用户有点赞记录 -> 基于向量相似度返回个性化推荐

    Args:
        db: 数据库会话
        user_id: 用户ID
        limit: 返回数量

    Returns:
        Dict[str, Any]: 推荐结果，包含：
            - article_ids: 推荐新闻ID列表
            - strategy: 推荐策略（"popular" 或 "personalized"）
    """
    # 1. 获取用户点赞的新闻ID
    liked_article_ids = get_user_liked_articles(db, user_id)

    if not liked_article_ids:
        # 场景1: 用户第一次登录（没有点赞记录）-> 返回热门新闻
        print(f"👤 用户 {user_id} 无点赞记录，使用热门新闻推荐")
        popular_ids = get_popular_articles(db, limit=limit, days=7)

        return {
            "article_ids": popular_ids,
            "strategy": "popular"
        }
    else:
        # 场景2: 用户有点赞记录 -> 使用个性化推荐
        print(f"👤 用户 {user_id} 有 {len(liked_article_ids)} 条点赞记录，使用个性化推荐")

        recommended_ids = get_personalized_recommendations(
            db=db,
            user_id=user_id,
            limit=limit,
            exclude_article_ids=liked_article_ids
        )

        # 如果个性化推荐结果不足，用热门新闻补充
        if len(recommended_ids) < limit:
            remaining = limit - len(recommended_ids)
            popular_ids = get_popular_articles(db, limit=remaining, days=7)

            # 过滤掉已推荐的和已点赞的
            additional_ids = [
                aid for aid in popular_ids
                if aid not in recommended_ids and aid not in liked_article_ids
            ]

            recommended_ids.extend(additional_ids[:remaining])

        return {
            "article_ids": recommended_ids,
            "strategy": "personalized"
        }
