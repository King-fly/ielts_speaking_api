"""
练习相关路由
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import json

from application.services.practice_service import PracticeService
from domain.models import User, PracticeTopic, PracticeSession, Assessment
from api.dependencies import get_db, get_current_active_user

router = APIRouter()


@router.get("/topics", response_model=List[Dict[str, Any]])
def get_practice_topics(
    part_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取练习话题列表
    
    Args:
        part_type: 话题类型（part1, part2, part3）
        difficulty: 难度级别（easy, medium, hard）
        category: 话题类别
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        List[Dict]: 话题列表
    """
    practice_service = PracticeService(db)
    
    # 获取话题列表
    topics = practice_service.get_practice_topics(
        part_type=part_type,
        difficulty=difficulty,
        category=category,
        skip=skip,
        limit=limit
    )
    
    # 转换为响应格式
    result = []
    for topic in topics:
        # 解析跟进问题
        follow_up_questions = []
        if topic.follow_up_questions:
            try:
                follow_up_questions = json.loads(topic.follow_up_questions)
            except json.JSONDecodeError:
                pass
        
        result.append({
            "id": topic.id,
            "title": topic.title,
            "description": topic.description,
            "category": topic.category,
            "difficulty_level": topic.difficulty_level,
            "part_type": topic.part_type,
            "follow_up_questions": follow_up_questions,
            "created_at": topic.created_at
        })
    
    return result


@router.get("/topics/{topic_id}", response_model=Dict[str, Any])
def get_practice_topic(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取特定练习话题
    
    Args:
        topic_id: 话题ID
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 话题详情
    """
    practice_service = PracticeService(db)
    
    # 获取话题
    topic = practice_service.get_topic_by_id(topic_id)
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    
    # 解析跟进问题
    follow_up_questions = []
    if topic.follow_up_questions:
        try:
            follow_up_questions = json.loads(topic.follow_up_questions)
        except json.JSONDecodeError:
            pass
    
    return {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "category": topic.category,
        "difficulty_level": topic.difficulty_level,
        "part_type": topic.part_type,
        "follow_up_questions": follow_up_questions,
        "created_at": topic.created_at
    }


@router.post("/topics/generate", response_model=Dict[str, Any])
def generate_topic(
    part_type: str = "general",
    difficulty: str = "medium",
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    生成新话题
    
    Args:
        part_type: 话题类型
        difficulty: 难度级别
        category: 话题类别
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 生成的话题
    """
    practice_service = PracticeService(db)
    
    try:
        # 生成话题
        topic = practice_service.generate_new_topic(
            part_type=part_type,
            difficulty=difficulty,
            category=category
        )
        
        # 解析跟进问题
        follow_up_questions = []
        if topic.follow_up_questions:
            try:
                follow_up_questions = json.loads(topic.follow_up_questions)
            except json.JSONDecodeError:
                pass
        
        return {
            "id": topic.id,
            "title": topic.title,
            "description": topic.description,
            "category": topic.category,
            "difficulty_level": topic.difficulty_level,
            "part_type": topic.part_type,
            "follow_up_questions": follow_up_questions,
            "created_at": topic.created_at
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate topic: {str(e)}"
        )


@router.post("/sessions", response_model=Dict[str, Any])
def create_practice_session(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建练习会话
    
    Args:
        topic_id: 话题ID
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 创建的会话
    """
    practice_service = PracticeService(db)
    
    # 验证话题是否存在
    topic = practice_service.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    
    # 创建会话
    session = practice_service.create_practice_session(current_user.id, topic_id)
    
    return {
        "id": session.id,
        "topic_id": session.topic_id,
        "topic_title": topic.title,
        "start_time": session.start_time,
        "status": session.status
    }


@router.post("/sessions/{session_id}/recordings", response_model=Dict[str, Any])
async def upload_recording(
    session_id: int,
    file: UploadFile = File(...),
    recording_order: int = Form(1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    上传语音记录
    
    Args:
        session_id: 会话ID
        file: 音频文件
        recording_order: 录音顺序
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 上传结果
    """
    practice_service = PracticeService(db)
    
    # 验证会话是否存在且属于当前用户
    session = practice_service.get_practice_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this session"
        )
    
    # 验证文件格式
    allowed_formats = ["wav", "mp3", "m4a", "ogg"]
    file_format = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_format not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed formats: {', '.join(allowed_formats)}"
        )
    
    # 读取文件数据
    file_data = await file.read()
    
    # 验证文件大小（最大10MB）
    max_size = 10 * 1024 * 1024  # 10MB
    if len(file_data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {max_size / (1024 * 1024)}MB"
        )
    
    # 保存录音
    recording = practice_service.save_speech_recording(
        session_id=session_id,
        file_data=file_data,
        file_format=file_format,
        file_name=file.filename,
        recording_order=recording_order
    )
    
    return {
        "id": recording.id,
        "session_id": recording.session_id,
        "file_path": recording.file_path,
        "file_format": recording.file_format,
        "recording_order": recording.recording_order,
        "created_at": recording.created_at,
        "message": "Recording uploaded successfully. Processing will begin shortly."
    }


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
def get_practice_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取练习会话
    
    Args:
        session_id: 会话ID
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 会话详情
    """
    practice_service = PracticeService(db)
    
    # 获取会话
    session = practice_service.get_practice_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this session"
        )
    
    # 获取评估结果
    assessment = practice_service.get_session_assessment(session_id)
    
    # 构建响应
    response = {
        "id": session.id,
        "topic_id": session.topic_id,
        "topic_title": session.topic.title if session.topic else None,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "duration_seconds": session.duration_seconds,
        "status": session.status,
        "recordings_count": len(session.recordings),
        "has_assessment": assessment is not None
    }
    
    # 如果有评估结果，添加到响应中
    if assessment:
        response["assessment"] = {
            "id": assessment.id,
            "overall_score": assessment.overall_score,
            "fluency_score": assessment.fluency_score,
            "pronunciation_score": assessment.pronunciation_score,
            "vocabulary_score": assessment.vocabulary_score,
            "grammar_score": assessment.grammar_score,
            "coherence_score": assessment.coherence_score,
            "created_at": assessment.created_at
        }
    
    return response


@router.get("/sessions/{session_id}/assessment", response_model=Dict[str, Any])
def get_session_assessment(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取会话评估结果
    
    Args:
        session_id: 会话ID
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 评估结果
    """
    practice_service = PracticeService(db)
    
    # 验证会话是否存在且属于当前用户
    session = practice_service.get_practice_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this session"
        )
    
    # 获取评估结果
    assessment = practice_service.get_session_assessment(session_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found for this session"
        )
    
    # 获取反馈列表
    feedback_items = practice_service.get_assessment_feedback(assessment.id)
    
    # 分类反馈
    strengths = []
    weaknesses = []
    suggestions = []
    
    for feedback in feedback_items:
        item = {
            "id": feedback.id,
            "description": feedback.description,
            "suggestion": feedback.suggestion,
            "severity": feedback.severity
        }
        
        if feedback.category == "strength":
            strengths.append(item)
        elif feedback.category == "weakness":
            weaknesses.append(item)
        elif feedback.category == "suggestion":
            suggestions.append(item)
    
    # 解析评估JSON数据
    assessment_data = {}
    if assessment.assessment_json:
        try:
            assessment_data = json.loads(assessment.assessment_json)
        except json.JSONDecodeError:
            pass
    
    return {
        "id": assessment.id,
        "session_id": session_id,
        "overall_score": assessment.overall_score,
        "fluency_score": assessment.fluency_score,
        "pronunciation_score": assessment.pronunciation_score,
        "vocabulary_score": assessment.vocabulary_score,
        "grammar_score": assessment.grammar_score,
        "coherence_score": assessment.coherence_score,
        "transcript": assessment.transcript,
        "feedback": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions
        },
        "detailed_feedback": assessment_data.get("feedback", ""),
        "created_at": assessment.created_at
    }


@router.get("/sessions", response_model=List[Dict[str, Any]])
def get_user_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户的练习会话列表
    
    Args:
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        List[Dict]: 会话列表
    """
    practice_service = PracticeService(db)
    
    # 获取会话列表
    sessions = practice_service.get_user_sessions(current_user.id, skip=skip, limit=limit)
    
    # 转换为响应格式
    result = []
    for session in sessions:
        result.append({
            "id": session.id,
            "topic_id": session.topic_id,
            "topic_title": session.topic.title if session.topic else None,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "duration_seconds": session.duration_seconds,
            "status": session.status,
            "has_assessment": len(session.assessments) > 0
        })
    
    return result