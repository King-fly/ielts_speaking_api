"""
对话处理相关的Celery任务
"""
import json
from datetime import datetime
from celery import Celery
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from shared.config.settings import get_settings
from infrastructure.database.database import SessionLocal
from infrastructure.external_services.openai_service import OpenAIService
from domain.models import DialogueSession, DialogueTurn, PracticeTopic

settings = get_settings()

# 创建Celery实例（复用speech_tasks中的实例）
from .speech_tasks import celery_app

# 创建服务实例
openai_service = OpenAIService()


@celery_app.task(bind=True)
def generate_dialogue_response(self, session_id: int, user_input: str, turn_number: int):
    """
    生成对话回应
    
    Args:
        self: Celery任务实例
        session_id: 对话会话ID
        user_input: 用户输入
        turn_number: 对话回合数
        
    Returns:
        Dict: 生成的回应
    """
    # 获取数据库会话
    db: Session = SessionLocal()
    
    try:
        # 获取对话会话
        session = db.query(DialogueSession).filter(DialogueSession.id == session_id).first()
        if not session:
            return {"error": "Dialogue session not found"}
        
        # 获取对话历史
        dialogue_history = db.query(DialogueTurn).filter(
            DialogueTurn.session_id == session_id
        ).order_by(DialogueTurn.turn_number).all()
        
        # 转换为OpenAI服务所需格式
        history_for_api = [
            {"speaker": turn.speaker, "content": turn.content}
            for turn in dialogue_history
        ]
        
        # 获取话题信息
        topic_info = None
        if session.topic:
            topic_info = session.topic.title
        
        # 生成AI回应
        ai_response = openai_service.generate_dialogue_response(
            context=topic_info or "General IELTS Speaking",
            user_input=user_input,
            dialogue_history=history_for_api,
            part_type=session.session_type,
            difficulty=session.difficulty_level
        )
        
        # 创建用户回合记录
        user_turn = DialogueTurn(
            session_id=session_id,
            turn_number=turn_number,
            speaker="user",
            content=user_input,
            created_at=datetime.utcnow()
        )
        db.add(user_turn)
        
        # 创建AI回合记录
        ai_turn = DialogueTurn(
            session_id=session_id,
            turn_number=turn_number + 1,
            speaker="ai_examiner",
            content=ai_response,
            created_at=datetime.utcnow()
        )
        db.add(ai_turn)
        
        # 更新会话信息
        session.total_turns = turn_number + 1
        session.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "session_id": session_id,
            "turn_number": turn_number + 1,
            "ai_response": ai_response,
            "total_turns": session.total_turns
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def create_initial_dialogue(self, session_id: int):
    """
    创建初始对话（考官开场白和第一个问题）
    
    Args:
        self: Celery任务实例
        session_id: 对话会话ID
        
    Returns:
        Dict: 初始对话信息
    """
    # 获取数据库会话
    db: Session = SessionLocal()
    
    try:
        # 获取对话会话
        session = db.query(DialogueSession).filter(DialogueSession.id == session_id).first()
        if not session:
            return {"error": "Dialogue session not found"}
        
        # 根据会话类型生成初始问题
        if session.topic:
            topic_title = session.topic.title
            topic_description = session.topic.description
            
            # 如果有预设问题，使用预设问题
            if session.topic.follow_up_questions:
                try:
                    questions = json.loads(session.topic.follow_up_questions)
                    if questions and isinstance(questions, list):
                        initial_question = questions[0]
                    else:
                        initial_question = f"让我们讨论一下关于{topic_title}的话题。你对此有什么看法？"
                except (json.JSONDecodeError, IndexError):
                    initial_question = f"让我们讨论一下关于{topic_title}的话题。你对此有什么看法？"
            else:
                initial_question = f"让我们讨论一下关于{topic_title}的话题。你对此有什么看法？"
        else:
            # 生成通用问题
            if session.session_type == "part1":
                initial_question = "你好，请简单介绍一下你自己，好吗？"
            elif session.session_type == "part2":
                initial_question = "我将给你一个话题，你有1分钟的准备时间，然后请说1-2分钟。你的话题是：描述一个对你有特殊意义的地方。"
            elif session.session_type == "part3":
                initial_question = "我们来讨论一些更深入的话题。你认为科技如何改变了人们的交流方式？"
            else:
                initial_question = "你好，今天我们来进行一场雅思口语练习。首先，请告诉我你来自哪里？"
        
        # 创建AI开场白回合
        开场白 = "你好，我是你的雅思口语考官。今天我们将进行一场口语练习。请放松，尽量自然地回答问题。准备好了吗？"
        opening_turn = DialogueTurn(
            session_id=session_id,
            turn_number=0,
            speaker="ai_examiner",
            content=开场白,
            created_at=datetime.utcnow()
        )
        db.add(opening_turn)
        
        # 创建AI问题回合
        question_turn = DialogueTurn(
            session_id=session_id,
            turn_number=1,
            speaker="ai_examiner",
            content=initial_question,
            created_at=datetime.utcnow()
        )
        db.add(question_turn)
        
        # 更新会话信息
        session.total_turns = 2
        session.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "session_id": session_id,
            "opening": 开场白,
            "initial_question": initial_question,
            "total_turns": 2
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()