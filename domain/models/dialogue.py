"""
对话相关领域模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .user import Base


class DialogueSession(Base):
    """对话会话模型"""
    __tablename__ = "dialogue_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("practice_topics.id"))
    session_type = Column(String(50), default="general")  # 如：general, part1, part2, part3
    difficulty_level = Column(String(20), default="medium")  # 如：easy, medium, hard
    status = Column(String(20), default="active")  # 如：active, completed, cancelled
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    total_turns = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="dialogue_sessions")
    topic = relationship("PracticeTopic")
    turns = relationship("DialogueTurn", back_populates="session", cascade="all, delete-orphan")


class DialogueTurn(Base):
    """对话回合模型"""
    __tablename__ = "dialogue_turns"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("dialogue_sessions.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    speaker = Column(String(20), nullable=False)  # 如：user, ai_examiner
    content = Column(Text, nullable=False)
    audio_path = Column(String(255))  # 用户语音路径
    is_feedback_provided = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("DialogueSession", back_populates="turns")