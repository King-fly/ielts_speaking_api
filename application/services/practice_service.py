"""
练习服务
"""
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from domain.models import PracticeTopic, PracticeSession, SpeechRecording, Assessment, FeedbackItem
from infrastructure.external_services.openai_service import OpenAIService
from infrastructure.tasks.speech_tasks import process_speech_recording

class PracticeService:
    """练习服务类"""
    
    def __init__(self, db: Session):
        """初始化练习服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.openai_service = OpenAIService()
    
    def get_practice_topics(self, part_type: Optional[str] = None, 
                          difficulty: Optional[str] = None,
                          category: Optional[str] = None,
                          skip: int = 0, limit: int = 20) -> List[PracticeTopic]:
        """
        获取练习话题列表
        
        Args:
            part_type: 话题类型（part1, part2, part3）
            difficulty: 难度级别（easy, medium, hard）
            category: 话题类别
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            List[PracticeTopic]: 话题列表
        """
        query = self.db.query(PracticeTopic)
        
        # 应用过滤条件
        if part_type:
            query = query.filter(PracticeTopic.part_type == part_type)
        if difficulty:
            query = query.filter(PracticeTopic.difficulty_level == difficulty)
        if category:
            query = query.filter(PracticeTopic.category == category)
        
        # 应用分页
        topics = query.order_by(desc(PracticeTopic.created_at)).offset(skip).limit(limit).all()
        
        return topics
    
    def get_topic_by_id(self, topic_id: int) -> Optional[PracticeTopic]:
        """
        通过ID获取话题
        
        Args:
            topic_id: 话题ID
            
        Returns:
            PracticeTopic: 话题对象，不存在则返回None
        """
        return self.db.query(PracticeTopic).filter(PracticeTopic.id == topic_id).first()
    
    def create_practice_session(self, user_id: int, topic_id: int) -> PracticeSession:
        """
        创建练习会话
        
        Args:
            user_id: 用户ID
            topic_id: 话题ID
            
        Returns:
            PracticeSession: 创建的练习会话
        """
        session = PracticeSession(
            user_id=user_id,
            topic_id=topic_id,
            start_time=datetime.utcnow(),
            status="in_progress"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def save_speech_recording(self, session_id: int, file_data: bytes, 
                            file_format: str, file_name: str,
                            recording_order: int = 1) -> SpeechRecording:
        """
        保存语音记录
        
        Args:
            session_id: 会话ID
            file_data: 音频文件数据
            file_format: 文件格式
            file_name: 文件名
            recording_order: 录音顺序
            
        Returns:
            SpeechRecording: 创建的语音记录
        """
        # 确保录音目录存在
        recordings_dir = "recordings"
        os.makedirs(recordings_dir, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_file_name = f"{session_id}_{timestamp}_{recording_order}.{file_format}"
        file_path = os.path.join(recordings_dir, unique_file_name)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        # 创建录音记录
        recording = SpeechRecording(
            session_id=session_id,
            file_path=file_path,
            file_format=file_format,
            recording_order=recording_order,
            size_bytes=len(file_data)
        )
        self.db.add(recording)
        self.db.commit()
        self.db.refresh(recording)
        
        # 异步处理录音
        process_speech_recording.delay(recording.id, file_path)
        
        return recording
    
    def get_practice_session(self, session_id: int) -> Optional[PracticeSession]:
        """
        获取练习会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            PracticeSession: 会话对象，不存在则返回None
        """
        return self.db.query(PracticeSession).filter(PracticeSession.id == session_id).first()
    
    def get_user_sessions(self, user_id: int, skip: int = 0, limit: int = 20) -> List[PracticeSession]:
        """
        获取用户的练习会话列表
        
        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            List[PracticeSession]: 会话列表
        """
        return self.db.query(PracticeSession).filter(
            PracticeSession.user_id == user_id
        ).order_by(desc(PracticeSession.created_at)).offset(skip).limit(limit).all()
    
    def get_session_assessment(self, session_id: int) -> Optional[Assessment]:
        """
        获取会话的评估结果
        
        Args:
            session_id: 会话ID
            
        Returns:
            Assessment: 评估结果，不存在则返回None
        """
        # 获取会话的所有录音
        recordings = self.db.query(SpeechRecording).filter(
            SpeechRecording.session_id == session_id
        ).all()
        
        if not recordings:
            return None
        
        # 获取最新录音的评估
        latest_recording = recordings[-1] if recordings else None
        if not latest_recording:
            return None
        
        return self.db.query(Assessment).filter(
            Assessment.recording_id == latest_recording.id
        ).first()
    
    def get_assessment_feedback(self, assessment_id: int) -> List[FeedbackItem]:
        """
        获取评估的反馈列表
        
        Args:
            assessment_id: 评估ID
            
        Returns:
            List[FeedbackItem]: 反馈列表
        """
        return self.db.query(FeedbackItem).filter(
            FeedbackItem.assessment_id == assessment_id
        ).all()
    
    def generate_new_topic(self, part_type: str = "general", 
                          difficulty: str = "medium",
                          category: Optional[str] = None) -> PracticeTopic:
        """
        生成新话题
        
        Args:
            part_type: 话题类型
            difficulty: 难度级别
            category: 话题类别
            
        Returns:
            PracticeTopic: 生成的话题
        """
        # 使用OpenAI生成话题
        topic_data = self.openai_service.generate_ielts_topic(part_type, difficulty)
        
        # 处理响应
        if isinstance(topic_data, dict):
            if "error" in topic_data:
                raise ValueError(f"Failed to generate topic: {topic_data['error']}")
        elif isinstance(topic_data, str):
            # 处理可能包含思考过程的响应
            import re
            # 提取JSON部分
            json_match = re.search(r'\{[^\}]*\}', topic_data)
            if json_match:
                json_str = json_match.group(0)
                try:
                    topic_data = json.loads(json_str)
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试清理字符串
                    # 移除可能的思考过程标记
                    clean_str = topic_data.replace('<think>', '').replace('</think>', '')
                    # 提取JSON部分
                    json_match = re.search(r'\{[^\}]*\}', clean_str)
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            topic_data = json.loads(json_str)
                        except json.JSONDecodeError:
                            raise ValueError("Failed to parse topic data: Invalid JSON format")
                    else:
                        raise ValueError("Failed to parse topic data: No JSON found")
            else:
                raise ValueError("Failed to parse topic data: No JSON found")
        else:
            raise ValueError("Failed to generate topic: Invalid response format")
        
        # 创建话题记录
        topic = PracticeTopic(
            title=topic_data.get("title", "New Topic"),
            description=topic_data.get("description", ""),
            category=category or topic_data.get("category", "general"),
            difficulty_level=difficulty,
            part_type=part_type,
            follow_up_questions=json.dumps(topic_data.get("questions", []))
        )
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)
        
        return topic