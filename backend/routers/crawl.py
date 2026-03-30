from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from database import get_db
from sqlalchemy.orm import Session
from models.article import Article

router = APIRouter(prefix="/api/crawl", tags=["crawl"])

class CrawlStartRequest(BaseModel):
    """爬虫启动请求参数"""
    source: Optional[str] = None  # 数据源：sina, pengpai 或 None(全部)
    use_rss: bool = True  # 是否使用RSS生成

@router.post("/start")
def start_crawl(
    request: CrawlStartRequest,
    db: Session = Depends(get_db)
):
    """
    启动爬虫任务
    """
    # TODO: 实现爬虫启动逻辑
    # 可以调用 rss_crawler.py 中的函数启动爬虫
    # 或将任务加入后台队列异步执行
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "source": request.source if request.source else "全部",
            "use_rss": request.use_rss,
            "status": "started"
        }
    }

@router.get("/status")
def get_crawl_status(db: Session = Depends(get_db)):
    """
    获取爬虫状态
    """
    
    total_count = db.query(Article).count()
    latest_article = db.query(Article).order_by(Article.created_at.desc()).first()
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "status": "idle",
            "latest_crawl_time": latest_article.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_article and latest_article.created_at else None,
            "total_articles": total_count
        }
    }
