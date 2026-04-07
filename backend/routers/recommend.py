# backend/routers/recommend.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.recommend_service import get_recommendations
from models.article import Article
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/recommend", tags=["recommend"])

@router.get("/")
def get_recommendations_endpoint(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取个性化推荐新闻列表

    推荐策略：
    1. 用户第一次登录（无点赞记录）-> 返回最近的热门新闻
    2. 用户非第一次登录（有点赞记录）-> 基于向量相似度返回个性化推荐

    Args:
        limit: 返回新闻数量，默认10条
        db: 数据库会话
        current_user: 当前登录用户（从JWT token中解析）

    Returns:
        {
            "code": 0,
            "message": "success",
            "data": [...],
            "strategy": "popular" 或 "personalized"
        }
    """
    try:
        user_id = current_user.id

        # 调用推荐服务
        result = get_recommendations(db, user_id, limit)
        recommended_items = result["article_ids"]
        strategy = result["strategy"]

        # 处理可能返回的是纯ID列表（兜底情况）或字典列表
        article_ids = []
        score_map = {}
        for item in recommended_items:
            if isinstance(item, dict):
                article_ids.append(item["id"])
                score_map[item["id"]] = item["score"]
            else:
                article_ids.append(item)
                score_map[item] = 0.5 # 默认匹配度

        if not article_ids:
            return {
                "code": 0,
                "message": "success",
                "data": [],
                "strategy": strategy,
                "count": 0
            }

        # 从数据库查询新闻详情
        articles = db.query(Article).filter(
            Article.id.in_(article_ids)
        ).all()

        # 按推荐顺序排序（保持 ID 顺序）
        article_dict = {a.id: a for a in articles}
        ordered_articles = [article_dict[aid] for aid in article_ids if aid in article_dict]

        # 动态计算用户的标签偏好比例
        # （根据用户点赞的历史新闻的标签来统计）
        from services.user_profile import get_user_liked_article_objects
        liked_articles = get_user_liked_article_objects(db, user_id)
        
        tag_counts = {}
        total_tags = 0
        for la in liked_articles:
            if la.tags:
                # 只取主分类（第一个标签）
                main_tag = la.tags.split(',')[0].strip()
                if main_tag:
                    tag_counts[main_tag] = tag_counts.get(main_tag, 0) + 1
                    total_tags += 1
        
        preferences = []
        if total_tags > 0:
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = int((count / total_tags) * 100)
                preferences.append({
                    "name": tag,
                    "score": percentage
                })
        else:
            # 兜底
            preferences = [
                {"name": "科技", "score": 85},
                {"name": "健康", "score": 62},
                {"name": "教育", "score": 45},
                {"name": "财经", "score": 30}
            ]

        # 格式化返回
        items = [
            {
                "id": a.id,
                "title": a.title,
                "summary": a.summary,
                "tags": a.tags,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "score": score_map.get(a.id, 0.5)
            }
            for a in ordered_articles
        ]

        return {
            "code": 0,
            "message": "success",
            "data": items,
            "strategy": strategy,
            "count": len(items),
            "preferences": preferences
        }

    except Exception as e:
        print(f"❌ 获取推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")