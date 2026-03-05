"""
认证相关依赖项
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from shared.config.settings import get_settings
from domain.models import User
from infrastructure.database.database import get_db

settings = get_settings()

# HTTP Bearer 认证
oauth2_scheme = HTTPBearer()


async def get_current_user(db: Session = Depends(get_db), 
                          token: str = Depends(oauth2_scheme)) -> User:
    """
    获取当前用户
    
    Args:
        db: 数据库会话
        token: HTTP Bearer令牌对象
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 从Bearer对象中提取token值
    token_value = token.credentials if hasattr(token, 'credentials') else token
    
    try:
        # 解码JWT令牌
        payload = jwt.decode(token_value, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 获取用户
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前活跃用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    return current_user