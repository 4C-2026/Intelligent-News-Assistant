from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models.base import Base
import os
import logging
from dotenv import load_dotenv
from routers import news, recommend, crawl, chat, user, interaction
import models   # 触发 __init__.py，所有模型注册到 Base.metadata

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建所有表
Base.metadata.create_all(bind=engine)


# ── 定时爬虫调度器 ────────────────────────────────────────────────────────
def _crawl_job():
    """APScheduler 定时任务：运行完整爬虫流水线"""
    logger.info("[Scheduler] 开始定时爬取任务...")
    try:
        from scraper.crawler_pipeline import run_full_pipeline
        stats = run_full_pipeline(max_items=15)
        logger.info(f"[Scheduler] 爬取完成: {stats}")
    except Exception as e:
        logger.error(f"[Scheduler] 爬取任务出错: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时开启调度器，关闭时停止"""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    # 每小时整点执行一次
    scheduler.add_job(_crawl_job, "interval", hours=1, id="auto_crawl")
    scheduler.start()
    logger.info("[Scheduler] 定时爬虫已启动，每小时自动爬取一次")

    # 启动后立即执行一次（可选，注释掉则等第一个整点再跑）
    _crawl_job()

    yield  # 应用运行中

    scheduler.shutdown(wait=False)
    logger.info("[Scheduler] 定时爬虫已停止")


app = FastAPI(lifespan=lifespan)

# ── CORS ──────────────────────────────────────────────────────────────────
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
origins.extend([
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://localhost:3000"
])
origins = list(set(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由 ──────────────────────────────────────────────────────────────────
app.include_router(news.router)
app.include_router(recommend.router)
app.include_router(crawl.router)
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(interaction.router)


@app.get("/")
def root():
    return {"message": "Intelligent News Assistant API"}
