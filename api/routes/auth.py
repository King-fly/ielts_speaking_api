"""
认证相关路由
"""
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from shared.config.settings import get_settings
from application.services.user_service import UserService
from domain.models import User
from api.dependencies import get_db, get_current_user, get_current_active_user

settings = get_settings()
router = APIRouter()


@router.post("/register", response_model=Dict[str, Any])
def register(
    username: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    用户注册
    
    Args:
        username: 用户名
        email: 邮箱
        password: 密码
        db: 数据库会话
        
    Returns:
        Dict: 包含用户信息的响应
        
    Raises:
        HTTPException: 用户名或邮箱已存在时抛出
    """
    user_service = UserService(db)
    
    # 检查用户名是否已存在
    if user_service.get_user_by_username(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 检查邮箱是否已存在
    if user_service.get_user_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建用户
    user = user_service.create_user(username, email, password)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message": "User registered successfully"
    }


@router.post("/login", response_model=Dict[str, Any])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    用户登录
    
    Args:
        form_data: OAuth2密码表单数据
        db: 数据库会话
        
    Returns:
        Dict: 包含访问令牌的响应
        
    Raises:
        HTTPException: 用户名或密码错误时抛出
    """
    user_service = UserService(db)
    
    # 验证用户
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }


@router.post("/refresh", response_model=Dict[str, Any])
def refresh_token(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    刷新访问令牌
    
    Args:
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 包含新访问令牌的响应
    """
    user_service = UserService(db)
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        data={"sub": current_user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# 导入依赖项（避免循环导入）
from api.dependencies.auth import get_current_active_user