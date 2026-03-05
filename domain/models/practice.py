"""
练习相关领域模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .user import Base


class PracticeTopic(Base):
    """口语练习话题模型"""
    __tablename__ = "practice_topics"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 如：daily life, education, technology
    difficulty_level = Column(String(20))  # 如：easy, medium, hard
    part_type = Column(String(20))  # 如：part1, part2, part3
    follow_up_questions = Column(Text)  # JSON格式存储跟进问题
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    practice_sessions = relationship("PracticeSession", back_populates="topic")


class PracticeSession(Base):
    """练习会话模型"""
    __tablename__ = "practice_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("practice_topics.id"), nullable=False)
    duration_seconds = Column(Integer)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(20), default="in_progress")  # 如：in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="practice_sessions")
    topic = relationship("PracticeTopic", back_populates="practice_sessions")
    recordings = relationship("SpeechRecording", back_populates="session", cascade="all, delete-orphan")
    assessments = relationship("Assessment", secondary="speech_recordings", back_populates="session", cascade="all")


class SpeechRecording(Base):
    """语音记录模型"""
    __tablename__ = "speech_recordings"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_format = Column(String(10))
    duration_seconds = Column(Float)
    size_bytes = Column(Integer)
    recording_order = Column(Integer)  # 同一会话中的录音顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("PracticeSession", back_populates="recordings")
    assessment = relationship("Assessment", back_populates="recording", uselist=False)


class Assessment(Base):
    """口语评估模型"""
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("speech_recordings.id"), unique=True, nullable=False)
    overall_score = Column(Float)
    fluency_score = Column(Float)
    pronunciation_score = Column(Float)
    vocabulary_score = Column(Float)
    grammar_score = Column(Float)
    coherence_score = Column(Float)
    transcript = Column(Text)
    assessment_json = Column(Text)  # 详细评估数据的JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    recording = relationship("SpeechRecording", back_populates="assessment")
    feedback_items = relationship("FeedbackItem", back_populates="assessment", cascade="all, delete-orphan")
    # 通过recording间接关联到session
    session = relationship("PracticeSession", secondary="speech_recordings", back_populates="assessments")


class FeedbackItem(Base):
    """反馈条目模型"""
    __tablename__ = "feedback_items"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    category = Column(String(50))  # 如：pronunciation, grammar, vocabulary
    description = Column(Text)
    suggestion = Column(Text)
    severity = Column(String(20))  # 如：minor, moderate, major
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    assessment = relationship("Assessment", back_populates="feedback_items")