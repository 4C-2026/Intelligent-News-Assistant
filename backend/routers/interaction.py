# interaction.py - 用户互动路由
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import User, Article, Interaction
from services.auth_service import get_current_user

router = APIRouter(prefix="/api", tags=["互动"])


class LikeRequest(BaseModel):
    article_id: int


class ReadRequest(BaseModel):
    article_id: int


@router.post("/like", summary="点赞新闻")
def like_article(
    request: LikeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户点赞新闻"""
    # 检查新闻是否存在
    article = db.query(Article).filter(Article.id == request.article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在"
        )
    
    # 检查是否已点赞
    existing = db.query(Interaction).filter(
        Interaction.user_id == current_user.id,
        Interaction.article_id == request.article_id,
        Interaction.action_type == "like"
    ).first()
    
    if existing:
        return {"code": 0, "message": "已点赞过", "data": {"liked": True}}
    
    # 记录点赞
    interaction = Interaction(
        user_id=current_user.id,
        article_id=request.article_id,
        action_type="like"
    )
    
    db.add(interaction)
    db.commit()
    
    return {"code": 0, "message": "点赞成功", "data": {"liked": True}}


@router.delete("/like", summary="取消点赞")
def unlike_article(
    request: LikeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消点赞"""
    like_record = db.query(Interaction).filter(
        Interaction.user_id == current_user.id,
        Interaction.article_id == request.article_id,
        Interaction.action_type == "like"
    ).first()
    
    if not like_record:
        return {"code": 0, "message": "未点赞过", "data": {"liked": False}}
    
    db.delete(like_record)
    db.commit()
    
    return {"code": 0, "message": "取消点赞成功", "data": {"liked": False}}


@router.post("/read", summary="记录阅读")
def record_read(
    request: ReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """记录用户阅读历史"""
    # 检查新闻是否存在
    article = db.query(Article).filter(Article.id == request.article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在"
        )
    
    existing = db.query(Interaction).filter(
        Interaction.user_id == current_user.id,
        Interaction.article_id == request.article_id,
        Interaction.action_type == "read"
    ).first()
    
    if existing:
        return {"code": 0, "message": "已记录阅读", "data": {"read": True}}
    
    interaction = Interaction(
        user_id=current_user.id,
        article_id=request.article_id,
        action_type="read"
    )
    
    db.add(interaction)
    db.commit()
    
    return {"code": 0, "message": "记录成功", "data": {"read": True}}


@router.get("/user/liked", summary="获取用户点赞的新闻")
def get_liked_articles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户点赞过的所有新闻ID"""
    likes = db.query(Interaction).filter(
        Interaction.user_id == current_user.id,
        Interaction.action_type == "like"
    ).all()
    
    article_ids = [like.article_id for like in likes]
    
    return {
        "code": 0,
        "data": {
            "article_ids": article_ids,
            "count": len(article_ids)
        }
    }


@router.get("/user/read", summary="获取用户阅读过的新闻")
def get_read_articles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户阅读过的所有新闻ID"""
    reads = db.query(Interaction).filter(
        Interaction.user_id == current_user.id,
        Interaction.action_type == "read"
    ).all()
    
    article_ids = [read.article_id for read in reads]
    
    return {
        "code": 0,
        "data": {
            "article_ids": article_ids,
            "count": len(article_ids)
        }
    }
