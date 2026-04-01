# backend/services/recommend_service.py
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from models.article import Article
from models.interaction import Interaction
from services.embedding_service import get_embedding
from services.vector_store import search_by_vector
import numpy as np
from datetime import datetime, timedelta
from sklearn.cluster import KMeans


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


def cluster_vectors(embeddings: List[List[float]], n_clusters: int = 3) -> List[List[int]]:
    """
    对向量列表进行聚类，返回每个簇的索引

    Args:
        embeddings: 向量列表
        n_clusters: 聚类数量，默认为3

    Returns:
        List[List[int]]: 每个簇包含的向量索引列表
    """
    if not embeddings:
        return []

    try:
        # 转换为numpy数组
        embeddings_array = np.array(embeddings)

        # 如果新闻数量小于聚类数，则调整聚类数
        actual_clusters = min(n_clusters, len(embeddings))

        # 使用K-means聚类
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings_array)

        # 按簇分组
        clusters = [[] for _ in range(actual_clusters)]
        for idx, label in enumerate(cluster_labels):
            clusters[label].append(idx)

        # 打印聚类结果
        print(f"📊 聚类结果：共 {actual_clusters} 个类别")
        for i, cluster in enumerate(clusters):
            print(f"   类别 {i + 1}: {len(cluster)} 篇新闻")

        return clusters

    except Exception as e:
        print(f"❌ 向量聚类失败: {e}")
        # 如果聚类失败，返回所有向量作为一个簇
        return [list(range(len(embeddings)))]


def get_article_vectors_with_ids(db: Session, article_ids: List[int]) -> Optional[Tuple[List[int], List[List[float]]]]:
    """
    获取新闻ID列表对应的向量

    Args:
        db: 数据库会话
        article_ids: 新闻ID列表

    Returns:
        Tuple[List[int], List[List[float]]] or None: (新闻ID列表, 向量列表)
    """
    if not article_ids:
        return None

    try:
        # 从数据库获取新闻内容
        articles = db.query(Article).filter(Article.id.in_(article_ids)).all()

        if not articles:
            return None

        # 获取每篇新闻的向量
        article_ids_list = []
        embeddings = []
        for article in articles:
            try:
                embedding = get_embedding(article.content)
                article_ids_list.append(article.id)
                embeddings.append(embedding)
            except Exception as e:
                print(f"⚠️ 新闻 {article.id} 向量化失败: {e}")
                continue

        if not embeddings:
            return None

        return article_ids_list, embeddings

    except Exception as e:
        print(f"❌ 获取新闻向量失败: {e}")
        return None


def get_personalized_recommendations(
    db: Session,
    user_id: int,
    limit: int = 10,
    exclude_article_ids: Optional[List[int]] = None
) -> List[int]:
    """
    基于用户点赞历史生成个性化推荐（使用向量相似度+聚类）

    逻辑：
    1. 获取用户点赞的新闻ID
    2. 获取这些新闻的向量
    3. 对向量进行聚类分类
    4. 每个类别分别计算平均向量
    5. 使用每个平均向量搜索相似新闻
    6. 合并结果并过滤

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

    # 2. 获取新闻向量
    result = get_article_vectors_with_ids(db, liked_article_ids)

    if not result:
        return []

    article_ids_list, embeddings = result

    if len(embeddings) == 0:
        return []

    # 3. 对向量进行聚类
    # 根据新闻数量决定聚类数量：新闻越多，聚类数越多
    n_clusters = min(3, len(embeddings))  # 最多3个类别
    clusters = cluster_vectors(embeddings, n_clusters=n_clusters)

    if not clusters:
        return []

    # 4. 每个类别分别计算平均向量并搜索相似新闻
    all_recommended_ids = []
    n_results_per_cluster = (limit * 2) // len(clusters) + 1  # 每个类别搜索的新闻数

    for cluster_indices in clusters:
        if not cluster_indices:
            continue

        # 获取该类别的向量
        cluster_embeddings = [embeddings[i] for i in cluster_indices]

        # 计算该类别的平均向量
        cluster_avg_vector = np.mean(cluster_embeddings, axis=0).tolist()

        # 使用该平均向量搜索相似新闻
        similar_ids = search_by_vector(cluster_avg_vector, n_results=n_results_per_cluster)

        if similar_ids:
            all_recommended_ids.extend(similar_ids)

    # 去重
    unique_recommended_ids = list(set(all_recommended_ids))

    # 5. 过滤掉用户已点赞的新闻和需要排除的新闻
    filtered_ids = [
        aid for aid in unique_recommended_ids
        if aid not in liked_article_ids and aid not in exclude_article_ids
    ]

    if not filtered_ids:
        return []

    # 6. 从数据库获取这些新闻，按发布时间排序（只返回最近的）
    recommended_articles = db.query(Article).filter(
        Article.id.in_(filtered_ids)
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
