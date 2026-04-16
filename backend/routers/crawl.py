import threading
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from database import get_db
from sqlalchemy.orm import Session
from models.article import Article

router = APIRouter(prefix="/api/crawl", tags=["crawl"])

# 爬虫运行状态（内存级，重启后重置）
_crawl_status = {
    "running": False,
    "last_run": None,
    "last_result": None,
}
_crawl_lock = threading.Lock()


class CrawlStartRequest(BaseModel):
    max_items: Optional[int] = 15  # 每个来源最多抓取的文章数


def _do_crawl(max_items: int):
    """后台线程中执行完整爬虫流水线"""
    import logging
    from datetime import datetime
    logger = logging.getLogger(__name__)

    with _crawl_lock:
        _crawl_status["running"] = True

    try:
        from scraper.crawler_pipeline import run_full_pipeline
        stats = run_full_pipeline(max_items=max_items)
        with _crawl_lock:
            _crawl_status["last_result"] = stats
        logger.info(f"[CrawlRouter] 手动爬取完成: {stats}")
    except Exception as e:
        logger.error(f"[CrawlRouter] 手动爬取失败: {e}")
        with _crawl_lock:
            _crawl_status["last_result"] = {"error": str(e)}
    finally:
        from datetime import datetime
        with _crawl_lock:
            _crawl_status["running"] = False
            _crawl_status["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@router.post("/start")
def start_crawl(
    request: CrawlStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    手动触发爬虫任务（后台异步执行，立即返回）。
    如果已有任务在运行，则拒绝重复启动。
    """
    with _crawl_lock:
        if _crawl_status["running"]:
            return {
                "code": 1,
                "message": "爬虫任务正在运行中，请稍后再试",
                "data": None,
            }

    # 在后台线程中执行，避免阻塞请求
    background_tasks.add_task(_do_crawl, request.max_items)

    return {
        "code": 0,
        "message": f"爬虫任务已启动（每源最多 {request.max_items} 条）",
        "data": {"max_items": request.max_items, "status": "started"},
    }


@router.get("/status")
def get_crawl_status(db: Session = Depends(get_db)):
    """
    查询爬虫当前状态及数据库统计。
    """
    total_count = db.query(Article).count()
    latest_article = (
        db.query(Article).order_by(Article.created_at.desc()).first()
    )

    with _crawl_lock:
        running = _crawl_status["running"]
        last_run = _crawl_status["last_run"]
        last_result = _crawl_status["last_result"]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "status": "running" if running else "idle",
            "last_run": last_run,
            "last_result": last_result,
            "latest_article_time": (
                latest_article.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if latest_article and latest_article.created_at
                else None
            ),
            "total_articles": total_count,
        },
    }
