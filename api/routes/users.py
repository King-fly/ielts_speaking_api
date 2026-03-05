"""
用户相关路由
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.services.user_service import UserService
from domain.models import User, UserProfile
from api.dependencies import get_db, get_current_active_user

router = APIRouter()


@router.get("/me", response_model=Dict[str, Any])
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取当前用户信息
    
    Args:
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 包含用户信息的响应
    """
    user_service = UserService(db)
    
    # 获取用户资料
    profile = user_service.get_user_by_id(current_user.id).profile
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "profile": {
            "full_name": profile.full_name if profile else None,
            "avatar_url": profile.avatar_url if profile else None,
            "ielts_target_score": profile.ielts_target_score if profile else None,
            "english_level": profile.english_level if profile else None
        } if profile else None
    }


@router.put("/profile", response_model=Dict[str, Any])
def update_user_profile(
    full_name: str = None,
    avatar_url: str = None,
    ielts_target_score: int = None,
    english_level: str = None,
    learning_preferences: Dict[str, Any] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新用户资料
    
    Args:
        full_name: 全名
        avatar_url: 头像URL
        ielts_target_score: 雅思目标分数
        english_level: 英语水平
        learning_preferences: 学习偏好
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 包含更新后资料的响应
    """
    user_service = UserService(db)
    
    # 准备更新数据
    update_data = {}
    if full_name is not None:
        update_data["full_name"] = full_name
    if avatar_url is not None:
        update_data["avatar_url"] = avatar_url
    if ielts_target_score is not None:
        # 验证雅思分数范围（1-9）
        if ielts_target_score < 1 or ielts_target_score > 9:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IELTS target score must be between 1 and 9"
            )
        update_data["ielts_target_score"] = ielts_target_score
    if english_level is not None:
        # 验证英语水平
        valid_levels = ["beginner", "intermediate", "advanced", "native"]
        if english_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"English level must be one of: {', '.join(valid_levels)}"
            )
        update_data["english_level"] = english_level
    if learning_preferences is not None:
        import json
        update_data["learning_preferences"] = json.dumps(learning_preferences)
    
    # 如果没有要更新的数据，返回错误
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update"
        )
    
    # 更新用户资料
    profile = user_service.update_user_profile(current_user.id, update_data)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return {
        "message": "Profile updated successfully",
        "profile": {
            "full_name": profile.full_name,
            "avatar_url": profile.avatar_url,
            "ielts_target_score": profile.ielts_target_score,
            "english_level": profile.english_level,
            "learning_preferences": json.loads(profile.learning_preferences) if profile.learning_preferences else None
        }
    }


@router.get("/progress", response_model=Dict[str, Any])
def get_user_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户学习进度
    
    Args:
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 包含学习进度的响应
    """
    user_service = UserService(db)
    
    # 获取用户进度
    progress = user_service.get_user_progress(current_user.id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User progress not found"
        )
    
    import json
    
    return {
        "total_practice_time_seconds": progress.total_practice_time_seconds,
        "total_sessions": progress.total_sessions,
        "total_dialogues": progress.total_dialogues,
        "average_score": progress.average_score,
        "fluency_improvement": progress.fluency_improvement,
        "pronunciation_improvement": progress.pronunciation_improvement,
        "vocabulary_improvement": progress.vocabulary_improvement,
        "grammar_improvement": progress.grammar_improvement,
        "coherence_improvement": progress.coherence_improvement,
        "last_practice_date": progress.last_practice_date,
        "streak_days": progress.streak_days,
        "weekly_activity": json.loads(progress.weekly_activity) if progress.weekly_activity else None,
        "skill_breakdown": json.loads(progress.skill_breakdown) if progress.skill_breakdown else None
    }