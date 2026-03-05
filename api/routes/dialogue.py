"""
对话相关路由
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import json

from application.services.dialogue_service import DialogueService
from domain.models import User, DialogueSession
from api.dependencies import get_db, get_current_active_user

router = APIRouter()


@router.post("/sessions", response_model=Dict[str, Any])
def create_dialogue_session(
    topic_id: Optional[int] = None,
    session_type: str = "general",
    difficulty_level: str = "medium",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建对话会话
    
    Args:
        topic_id: 话题ID（可选）
        session_type: 会话类型（general, part1, part2, part3）
        difficulty_level: 难度级别（easy, medium, hard）
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 创建的会话
    """
    dialogue_service = DialogueService(db)
    
    try:
        # 创建会话
        session = dialogue_service.create_dialogue_session(
            user_id=current_user.id,
            topic_id=topic_id,
            session_type=session_type,
            difficulty_level=difficulty_level
        )
        
        return {
            "id": session.id,
            "topic_id": session.topic_id,
            "session_type": session.session_type,
            "difficulty_level": session.difficulty_level,
            "status": session.status,
            "start_time": session.start_time,
            "message": "Dialogue session created successfully. Initial questions are being generated."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dialogue session: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
def get_dialogue_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取对话会话
    
    Args:
        session_id: 会话ID
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 会话详情
    """
    dialogue_service = DialogueService(db)
    
    # 获取会话
    session = dialogue_service.get_dialogue_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dialogue session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this session"
        )
    
    # 获取对话回合
    turns = dialogue_service.get_dialogue_turns(session_id)
    
    # 转换为响应格式
    dialogue_history = []
    for turn in turns:
        dialogue_history.append({
            "turn_number": turn.turn_number,
            "speaker": turn.speaker,
            "content": turn.content,
            "created_at": turn.created_at
        })
    
    return {
        "id": session.id,
        "topic_id": session.topic_id,
        "topic_title": session.topic.title if session.topic else None,
        "session_type": session.session_type,
        "difficulty_level": session.difficulty_level,
        "status": session.status,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "total_turns": session.total_turns,
        "dialogue_history": dialogue_history
    }


@router.post("/sessions/{session_id}/turns", response_model=Dict[str, Any])
def submit_user_response(
    session_id: int,
    content: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    提交用户回应
    
    Args:
        session_id: 会话ID
        content: 用户回应内容
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 提交结果
    """
    dialogue_service = DialogueService(db)
    
    # 验证会话是否存在且属于当前用户
    session = dialogue_service.get_dialogue_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dialogue session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this session"
        )
    
    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dialogue session is not active"
        )
    
    try:
        # 提交用户回应
        result = dialogue_service.submit_user_response(session_id, content)
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process your response: {str(e)}"
        )


@router.get("/sessions/{session_id}/turns", response_model=List[Dict[str, Any]])
def get_dialogue_turns(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取对话回合列表
    
    Args:
        session_id: 会话ID
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        List[Dict]: 对话回合列表
    """
    dialogue_service = DialogueService(db)
    
    # 验证会话是否存在且属于当前用户
    session = dialogue_service.get_dialogue_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dialogue session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this session"
        )
    
    # 获取对话回合
    turns = dialogue_service.get_dialogue_turns(session_id)
    
    # 转换为响应格式
    result = []
    for turn in turns:
        result.append({
            "turn_number": turn.turn_number,
            "speaker": turn.speaker,
            "content": turn.content,
            "created_at": turn.created_at
        })
    
    return result


@router.post("/sessions/{session_id}/end", response_model=Dict[str, Any])
def end_dialogue_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    结束对话会话
    
    Args:
        session_id: 会话ID
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 结束结果
    """
    dialogue_service = DialogueService(db)
    
    # 验证会话是否存在且属于当前用户
    session = dialogue_service.get_dialogue_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dialogue session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this session"
        )
    
    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dialogue session is not active"
        )
    
    try:
        # 结束会话
        session = dialogue_service.end_dialogue_session(session_id)
        
        return {
            "id": session.id,
            "status": session.status,
            "end_time": session.end_time,
            "message": "Dialogue session ended successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end dialogue session: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取对话生成任务状态
    
    Args:
        task_id: Celery任务ID
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 任务状态和结果
    """
    dialogue_service = DialogueService(db)
    
    try:
        # 获取任务状态
        status = dialogue_service.get_dialogue_task_status(task_id)
        
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/sessions", response_model=List[Dict[str, Any]])
def get_user_dialogue_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户的对话会话列表
    
    Args:
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        List[Dict]: 会话列表
    """
    dialogue_service = DialogueService(db)
    
    # 获取会话列表
    sessions = dialogue_service.get_user_dialogue_sessions(current_user.id, skip=skip, limit=limit)
    
    # 转换为响应格式
    result = []
    for session in sessions:
        result.append({
            "id": session.id,
            "topic_id": session.topic_id,
            "topic_title": session.topic.title if session.topic else None,
            "session_type": session.session_type,
            "difficulty_level": session.difficulty_level,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "total_turns": session.total_turns
        })
    
    return result