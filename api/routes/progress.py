"""
学习进度相关路由
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
from datetime import datetime, timedelta

from application.services.user_service import UserService
from application.services.practice_service import PracticeService
from application.services.dialogue_service import DialogueService
from domain.models import User, LearningProgress, PracticeSession, DialogueSession, Assessment, SpeechRecording
from api.dependencies import get_db, get_current_active_user

router = APIRouter()


@router.get("/overview", response_model=Dict[str, Any])
def get_progress_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取学习进度概览
    
    Args:
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 学习进度概览
    """
    user_service = UserService(db)
    practice_service = PracticeService(db)
    
    # 获取用户进度
    progress = user_service.get_user_progress(current_user.id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User progress not found"
        )
    
    # 获取最近的练习会话
    recent_sessions = db.query(PracticeSession).filter(
        PracticeSession.user_id == current_user.id
    ).order_by(desc(PracticeSession.created_at)).limit(5).all()
    
    # 获取最近的评估结果
    recent_assessments = []
    for session in recent_sessions:
        if session.assessments:
            assessment = session.assessments[-1] if session.assessments else None
            if assessment:
                recent_assessments.append({
                    "session_id": session.id,
                    "topic_title": session.topic.title if session.topic else "Unknown Topic",
                    "date": assessment.created_at,
                    "overall_score": assessment.overall_score,
                    "fluency_score": assessment.fluency_score,
                    "pronunciation_score": assessment.pronunciation_score,
                    "vocabulary_score": assessment.vocabulary_score,
                    "grammar_score": assessment.grammar_score,
                    "coherence_score": assessment.coherence_score
                })
    
    # 计算学习趋势
    # 获取过去7天的每日练习时间
    daily_activity = []
    today = datetime.utcnow().date()
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = datetime.combine(date, datetime.max.time())
        
        # 计算当天的练习时间
        day_sessions = db.query(PracticeSession).filter(
            PracticeSession.user_id == current_user.id,
            PracticeSession.start_time >= start_datetime,
            PracticeSession.start_time <= end_datetime
        ).all()
        
        total_seconds = sum(session.duration_seconds or 0 for session in day_sessions)
        
        daily_activity.append({
            "date": date.isoformat(),
            "minutes": round(total_seconds / 60, 1)
        })
    
    # 解析技能细分数据
    skill_breakdown = {}
    if progress.skill_breakdown:
        try:
            skill_breakdown = json.loads(progress.skill_breakdown)
        except json.JSONDecodeError:
            pass
    
    return {
        "total_practice_time_minutes": round(progress.total_practice_time_seconds / 60, 1),
        "total_sessions": progress.total_sessions,
        "total_dialogues": progress.total_dialogues,
        "average_score": progress.average_score,
        "last_practice_date": progress.last_practice_date,
        "streak_days": progress.streak_days,
        "skill_improvement": {
            "fluency": progress.fluency_improvement,
            "pronunciation": progress.pronunciation_improvement,
            "vocabulary": progress.vocabulary_improvement,
            "grammar": progress.grammar_improvement,
            "coherence": progress.coherence_improvement
        },
        "daily_activity": daily_activity,
        "skill_breakdown": skill_breakdown,
        "recent_assessments": recent_assessments[:5]  # 最多返回5个
    }


@router.get("/history", response_model=Dict[str, Any])
def get_progress_history(
    period: str = "week",  # week, month, year
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取学习历史记录
    
    Args:
        period: 时间周期（week, month, year）
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 学习历史记录
    """
    # 计算时间范围
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid period. Must be one of: week, month, year"
        )
    
    # 获取练习会话
    practice_sessions = db.query(PracticeSession).filter(
        PracticeSession.user_id == current_user.id,
        PracticeSession.created_at >= start_date
    ).order_by(desc(PracticeSession.created_at)).offset(skip).limit(limit).all()
    
    # 获取对话会话
    dialogue_sessions = db.query(DialogueSession).filter(
        DialogueSession.user_id == current_user.id,
        DialogueSession.created_at >= start_date
    ).order_by(desc(DialogueSession.created_at)).offset(skip).limit(limit).all()
    
    # 转换为响应格式
    practice_history = []
    for session in practice_sessions:
        # 获取评估结果
        assessment = None
        if session.assessments:
            assessment = session.assessments[-1]
        
        practice_history.append({
            "id": session.id,
            "type": "practice",
            "topic_title": session.topic.title if session.topic else "Unknown Topic",
            "date": session.created_at,
            "duration_minutes": round(session.duration_seconds / 60, 1) if session.duration_seconds else None,
            "status": session.status,
            "score": assessment.overall_score if assessment else None
        })
    
    dialogue_history = []
    for session in dialogue_sessions:
        dialogue_history.append({
            "id": session.id,
            "type": "dialogue",
            "topic_title": session.topic.title if session.topic else "General Discussion",
            "date": session.created_at,
            "duration_minutes": round((session.end_time - session.start_time).total_seconds() / 60, 1) 
                               if session.end_time and session.start_time else None,
            "status": session.status,
            "total_turns": session.total_turns
        })
    
    # 合并并按日期排序
    all_history = practice_history + dialogue_history
    all_history.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "period": period,
        "total_practice_sessions": len(practice_history),
        "total_dialogue_sessions": len(dialogue_history),
        "history": all_history
    }


@router.get("/analytics", response_model=Dict[str, Any])
def get_progress_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取学习分析数据
    
    Args:
        current_user: 当前活跃用户
        db: 数据库会话
        
    Returns:
        Dict: 学习分析数据
    """
    # 获取用户所有的评估结果
    assessments = db.query(Assessment).join(
        SpeechRecording
    ).join(
        PracticeSession
    ).filter(
        PracticeSession.user_id == current_user.id
    ).order_by(Assessment.created_at).all()
    
    if not assessments:
        return {
            "message": "No assessment data available",
            "has_data": False
        }
    
    # 计算各项技能的趋势
    fluency_scores = [a.fluency_score for a in assessments]
    pronunciation_scores = [a.pronunciation_score for a in assessments]
    vocabulary_scores = [a.vocabulary_score for a in assessments]
    grammar_scores = [a.grammar_score for a in assessments]
    coherence_scores = [a.coherence_score for a in assessments]
    overall_scores = [a.overall_score for a in assessments]
    
    # 计算平均分和最高分
    avg_fluency = sum(fluency_scores) / len(fluency_scores) if fluency_scores else 0
    avg_pronunciation = sum(pronunciation_scores) / len(pronunciation_scores) if pronunciation_scores else 0
    avg_vocabulary = sum(vocabulary_scores) / len(vocabulary_scores) if vocabulary_scores else 0
    avg_grammar = sum(grammar_scores) / len(grammar_scores) if grammar_scores else 0
    avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0
    avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    
    max_fluency = max(fluency_scores) if fluency_scores else 0
    max_pronunciation = max(pronunciation_scores) if pronunciation_scores else 0
    max_vocabulary = max(vocabulary_scores) if vocabulary_scores else 0
    max_grammar = max(grammar_scores) if grammar_scores else 0
    max_coherence = max(coherence_scores) if coherence_scores else 0
    max_overall = max(overall_scores) if overall_scores else 0
    
    # 计算进步幅度（最近三次的平均分减去前三次的平均分）
    progress_period = min(3, len(assessments) // 2)
    
    fluency_progress = 0
    pronunciation_progress = 0
    vocabulary_progress = 0
    grammar_progress = 0
    coherence_progress = 0
    overall_progress = 0
    
    if len(assessments) >= progress_period * 2:
        recent_fluency = sum(fluency_scores[-progress_period:]) / progress_period
        early_fluency = sum(fluency_scores[:progress_period]) / progress_period
        fluency_progress = recent_fluency - early_fluency
        
        recent_pronunciation = sum(pronunciation_scores[-progress_period:]) / progress_period
        early_pronunciation = sum(pronunciation_scores[:progress_period]) / progress_period
        pronunciation_progress = recent_pronunciation - early_pronunciation
        
        recent_vocabulary = sum(vocabulary_scores[-progress_period:]) / progress_period
        early_vocabulary = sum(vocabulary_scores[:progress_period]) / progress_period
        vocabulary_progress = recent_vocabulary - early_vocabulary
        
        recent_grammar = sum(grammar_scores[-progress_period:]) / progress_period
        early_grammar = sum(grammar_scores[:progress_period]) / progress_period
        grammar_progress = recent_grammar - early_grammar
        
        recent_coherence = sum(coherence_scores[-progress_period:]) / progress_period
        early_coherence = sum(coherence_scores[:progress_period]) / progress_period
        coherence_progress = recent_coherence - early_coherence
        
        recent_overall = sum(overall_scores[-progress_period:]) / progress_period
        early_overall = sum(overall_scores[:progress_period]) / progress_period
        overall_progress = recent_overall - early_overall
    
    # 找出最强和最弱的技能
    skills = [
        ("fluency", avg_fluency),
        ("pronunciation", avg_pronunciation),
        ("vocabulary", avg_vocabulary),
        ("grammar", avg_grammar),
        ("coherence", avg_coherence)
    ]
    
    strongest_skill = max(skills, key=lambda x: x[1])
    weakest_skill = min(skills, key=lambda x: x[1])
    
    # 准备图表数据
    chart_data = {
        "dates": [a.created_at.strftime("%Y-%m-%d") for a in assessments],
        "fluency": fluency_scores,
        "pronunciation": pronunciation_scores,
        "vocabulary": vocabulary_scores,
        "grammar": grammar_scores,
        "coherence": coherence_scores,
        "overall": overall_scores
    }
    
    return {
        "has_data": True,
        "total_assessments": len(assessments),
        "average_scores": {
            "fluency": round(avg_fluency, 1),
            "pronunciation": round(avg_pronunciation, 1),
            "vocabulary": round(avg_vocabulary, 1),
            "grammar": round(avg_grammar, 1),
            "coherence": round(avg_coherence, 1),
            "overall": round(avg_overall, 1)
        },
        "max_scores": {
            "fluency": max_fluency,
            "pronunciation": max_pronunciation,
            "vocabulary": max_vocabulary,
            "grammar": max_grammar,
            "coherence": max_coherence,
            "overall": max_overall
        },
        "progress": {
            "fluency": round(fluency_progress, 1),
            "pronunciation": round(pronunciation_progress, 1),
            "vocabulary": round(vocabulary_progress, 1),
            "grammar": round(grammar_progress, 1),
            "coherence": round(coherence_progress, 1),
            "overall": round(overall_progress, 1)
        },
        "skill_ranking": {
            "strongest": strongest_skill[0],
            "strongest_score": round(strongest_skill[1], 1),
            "weakest": weakest_skill[0],
            "weakest_score": round(weakest_skill[1], 1)
        },
        "chart_data": chart_data
    }