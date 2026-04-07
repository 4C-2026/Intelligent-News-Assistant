from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.news_service import NewsService

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("/")
def get_news(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    result = NewsService.get_news_list(db, page, size)
    return {
        "code": 0,
        "message": "success",
        **result   # 将 data, total, page, size 展开到返回字典中
    }

@router.get("/{news_id}")
def get_news_detail(news_id: int, db: Session = Depends(get_db)):
    detail = NewsService.get_news_detail(db, news_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="新闻不存在")
        
    # 获取相关推荐
    try:
        from services.vector_store import search_by_vector
        from services.embedding_service import get_embedding
        
        # 1. 对当前新闻正文或摘要进行向量化
        content_to_embed = detail.get("content") or detail.get("summary") or detail.get("title")
        if content_to_embed:
            query_vector = get_embedding(content_to_embed)
            
            # 2. 从 ChromaDB 检索相似新闻（多取几条以便过滤掉自己）
            similar_items = search_by_vector(query_vector, n_results=6)
            
            related_ids = []
            for item in similar_items:
                # search_by_vector 现在返回的是 List[Tuple[int, float]]
                aid = item[0] if isinstance(item, tuple) else item
                if aid != news_id:
                    related_ids.append(aid)
                    
            # 3. 限制只返回 3 条相关推荐
            related_ids = related_ids[:3]
            
            # 4. 从数据库获取这些新闻的详情
            if related_ids:
                from models.article import Article
                related_articles = db.query(Article).filter(Article.id.in_(related_ids)).all()
                
                detail["related"] = [
                    {
                        "id": a.id,
                        "title": a.title,
                        "summary": a.summary or "暂无摘要"
                    }
                    for a in related_articles
                ]
    except Exception as e:
        print(f"❌ 获取相关推荐失败: {e}")
        # 失败则不返回 related 字段
        
    return {
        "code": 0,
        "message": "success",
        "data": detail
    }
