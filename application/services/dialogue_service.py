"""
对话服务
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from domain.models import DialogueSession, DialogueTurn, PracticeTopic
from infrastructure.tasks.dialogue_tasks import create_initial_dialogue, generate_dialogue_response

class DialogueService:
    """对话服务类"""
    
    def __init__(self, db: Session):
        """初始化对话服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def create_dialogue_session(self, user_id: int, topic_id: Optional[int] = None,
                              session_type: str = "general",
                              difficulty_level: str = "medium") -> DialogueSession:
        """
        创建对话会话
        
        Args:
            user_id: 用户ID
            topic_id: 话题ID（可选）
            session_type: 会话类型（general, part1, part2, part3）
            difficulty_level: 难度级别（easy, medium, hard）
            
        Returns:
            DialogueSession: 创建的对话会话
        """
        # 验证话题是否存在
        topic = None
        if topic_id:
            topic = self.db.query(PracticeTopic).filter(PracticeTopic.id == topic_id).first()
            if not topic:
                raise ValueError(f"Topic with id {topic_id} not found")
        
        # 创建会话
        session = DialogueSession(
            user_id=user_id,
            topic_id=topic_id,
            session_type=session_type,
            difficulty_level=difficulty_level,
            status="active",
            start_time=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # 异步创建初始对话
        create_initial_dialogue.delay(session.id)
        
        return session
    
    def get_dialogue_session(self, session_id: int) -> Optional[DialogueSession]:
        """
        获取对话会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            DialogueSession: 会话对象，不存在则返回None
        """
        return self.db.query(DialogueSession).filter(DialogueSession.id == session_id).first()
    
    def get_user_dialogue_sessions(self, user_id: int, skip: int = 0, limit: int = 20) -> List[DialogueSession]:
        """
        获取用户的对话会话列表
        
        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            List[DialogueSession]: 会话列表
        """
        return self.db.query(DialogueSession).filter(
            DialogueSession.user_id == user_id
        ).order_by(desc(DialogueSession.created_at)).offset(skip).limit(limit).all()
    
    def get_dialogue_turns(self, session_id: int) -> List[DialogueTurn]:
        """
        获取对话回合列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[DialogueTurn]: 回合列表
        """
        return self.db.query(DialogueTurn).filter(
            DialogueTurn.session_id == session_id
        ).order_by(DialogueTurn.turn_number).all()
    
    def submit_user_response(self, session_id: int, user_input: str, 
                           audio_path: Optional[str] = None) -> Dict[str, Any]:
        """
        提交用户回应并生成AI回应
        
        Args:
            session_id: 会话ID
            user_input: 用户输入文本
            audio_path: 音频文件路径（可选）
            
        Returns:
            Dict: 包含AI回应的结果
        """
        # 获取会话
        session = self.get_dialogue_session(session_id)
        if not session:
            raise ValueError(f"Dialogue session with id {session_id} not found")
        
        if session.status != "active":
            raise ValueError("Dialogue session is not active")
        
        # 获取当前回合数
        last_turn = self.db.query(DialogueTurn).filter(
            DialogueTurn.session_id == session_id
        ).order_by(desc(DialogueTurn.turn_number)).first()
        
        if not last_turn:
            # 如果没有回合记录，从0开始
            current_turn = 0
        else:
            # 如果最后一个回合是用户的，说明用户连续提交了两次
            if last_turn.speaker == "user":
                raise ValueError("Please wait for the AI response before submitting another response")
            current_turn = last_turn.turn_number + 1
        
        # 异步生成AI回应
        task_result = generate_dialogue_response.delay(session_id, user_input, current_turn)
        
        return {
            "session_id": session_id,
            "task_id": task_result.id,
            "status": "processing",
            "message": "Your response has been submitted. AI response is being generated."
        }
    
    def end_dialogue_session(self, session_id: int) -> DialogueSession:
        """
        结束对话会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            DialogueSession: 更新后的会话对象
        """
        session = self.get_dialogue_session(session_id)
        if not session:
            raise ValueError(f"Dialogue session with id {session_id} not found")
        
        session.status = "completed"
        session.end_time = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_dialogue_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取对话生成任务状态
        
        Args:
            task_id: Celery任务ID
            
        Returns:
            Dict: 任务状态和结果
        """
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        if result.ready():
            if result.successful():
                return {
                    "status": "completed",
                    "result": result.get()
                }
            else:
                return {
                    "status": "failed",
                    "error": str(result.result)
                }
        else:
            return {
                "status": "processing",
                "message": "AI response is still being generated"
            }