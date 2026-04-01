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
    return {
        "code": 0,
        "message": "success",
        "data": detail
    }