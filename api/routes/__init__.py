"""
API路由
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .practice import router as practice_router
from .dialogue import router as dialogue_router
from .progress import router as progress_router

# 创建主路由
api_router = APIRouter()

# 包含子路由
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(practice_router, prefix="/practice", tags=["practice"])
api_router.include_router(dialogue_router, prefix="/dialogue", tags=["dialogue"])
api_router.include_router(progress_router, prefix="/progress", tags=["progress"])