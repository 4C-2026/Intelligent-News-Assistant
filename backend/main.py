from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models.base import Base
import os
from dotenv import load_dotenv
from routers import news, recommend, crawl
import models   # 这会触发 __init__.py 中的导入，所有模型都被注册到 Base.metadata

load_dotenv()

# 创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 配置 CORS（允许前端访问）
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(news.router)
app.include_router(recommend.router)
app.include_router(crawl.router)

@app.get("/")
def root():
    return {"message": "Hello World"}


