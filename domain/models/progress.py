"""
学习进度相关领域模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from .user import Base


class LearningProgress(Base):
    """学习进度模型"""
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_practice_time_seconds = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    total_dialogues = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    fluency_improvement = Column(Float, default=0.0)
    pronunciation_improvement = Column(Float, default=0.0)
    vocabulary_improvement = Column(Float, default=0.0)
    grammar_improvement = Column(Float, default=0.0)
    coherence_improvement = Column(Float, default=0.0)
    last_practice_date = Column(DateTime)
    streak_days = Column(Integer, default=0)
    weekly_activity = Column(Text)  # JSON格式存储每周活动数据
    skill_breakdown = Column(Text)  # JSON格式存储技能细分数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="learning_progress")