from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import User
from services.auth_service import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta

router = APIRouter(prefix="/api/user", tags=["用户"])


# ===== 请求/响应模型 =====
class UserRegisterRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict


# ===== 接口实现 =====
@router.post("/register", summary="用户注册")
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 1. 检查用户名是否已存在
    existing_user = db.query(User).filter(
        User.username == request.username
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 2. 创建新用户
    hashed_password = hash_password(request.password)
    new_user = User(
        username=request.username,
        password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"code": 0, "message": "注册成功", "data": {"user_id": new_user.id}}


@router.post("/login", summary="用户登录")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录，返回 JWT Token"""
   
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "code": 0,
        "message": "登录成功",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }
    }


@router.get("/profile", summary="获取当前用户信息")
def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息（需要认证）"""
    return {
        "code": 0,
        "data": {
            "id": current_user.id,
            "username": current_user.username
        }
    }