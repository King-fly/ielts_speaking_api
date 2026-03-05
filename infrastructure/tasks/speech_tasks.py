"""
语音处理相关的Celery任务
"""
import json
import os
from datetime import datetime
from celery import Celery
from sqlalchemy.orm import Session

from shared.config.settings import get_settings
from infrastructure.database.database import SessionLocal
from infrastructure.external_services.speech_service import SpeechService
from infrastructure.external_services.openai_service import OpenAIService
from domain.models import SpeechRecording, Assessment, FeedbackItem, PracticeSession, LearningProgress

settings = get_settings()

# 创建Celery实例
celery_app = Celery(
    'speech_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# 配置Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# 创建服务实例
speech_service = SpeechService()
openai_service = OpenAIService()


@celery_app.task(bind=True)
def process_speech_recording(self, recording_id: int, file_path: str, language: str = "en-US"):
    """
    处理语音录制并进行转录
    
    Args:
        self: Celery任务实例
        recording_id: 录音ID
        file_path: 音频文件路径
        language: 音频语言代码
        
    Returns:
        Dict: 处理结果
    """
    # 获取数据库会话
    db: Session = SessionLocal()
    
    try:
        # 转录音频
        transcript, metadata = speech_service.transcribe_audio_file(file_path, language)
        
        if not transcript:
            return {"error": "Failed to transcribe audio", "details": metadata}
        
        # 更新录音记录
        recording = db.query(SpeechRecording).filter(SpeechRecording.id == recording_id).first()
        if recording:
            recording.duration_seconds = metadata.get("duration_seconds", 0)
            recording.size_bytes = metadata.get("file_size_bytes", 0)
            db.commit()
        
        # 创建评估任务
        评估_result = evaluate_speech.delay(recording_id, transcript)
        
        return {
            "recording_id": recording_id,
            "transcript": transcript,
            "metadata": metadata,
            "assessment_task_id":评估_result.id
        }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def evaluate_speech(self, recording_id: int, transcript: str):
    """
    评估语音表现
    
    Args:
        self: Celery任务实例
        recording_id: 录音ID
        transcript: 转录文本
        
    Returns:
        Dict: 评估结果
    """
    # 获取数据库会话
    db: Session = SessionLocal()
    
    try:
        # 获取录音记录
        recording = db.query(SpeechRecording).filter(SpeechRecording.id == recording_id).first()
        if not recording:
            return {"error": "Recording not found"}
        
        # 获取相关会话和话题
        session = db.query(PracticeSession).filter(PracticeSession.id == recording.session_id).first()
        if not session:
            return {"error": "Session not found"}
        
        topic_title = session.topic.title if session.topic else None
        
        # 使用OpenAI评估口语表现
        评估_result = openai_service.evaluate_speech_transcript(transcript, topic_title)
        
        # 解析评估结果
        if isinstance(评估_result, str):
            # 处理可能包含思考过程的响应
            import re
            # 提取JSON部分
            json_match = re.search(r'\{[^\}]*\}', 评估_result)
            if json_match:
                json_str = json_match.group(0)
                try:
                    评估_data = json.loads(json_str)
                except json.JSONDecodeError:
                    # 清理字符串并重新尝试提取JSON
                    clean_str = 评估_result.replace('</think>', '').replace('', '')
                    json_match = re.search(r'\{[^\}]*\}', clean_str)
                    if json_match:
                        try:
                            评估_data = json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            return {"error": "Failed to parse assessment JSON"}
                    else:
                        return {"error": "No valid JSON found in assessment result"}
            else:
                return {"error": "No valid JSON found in assessment result"}
        else:
            评估_data = 评估_result
        
        if "error" in 评估_data:
            return 评估_data
        
        # 创建评估记录
        assessment = Assessment(
            recording_id=recording_id,
            overall_score=评估_data.get("overall_score", 0),
            fluency_score=评估_data.get("fluency_score", 0),
            pronunciation_score=评估_data.get("pronunciation_score", 0),
            vocabulary_score=评估_data.get("vocabulary_score", 0),
            grammar_score=评估_data.get("grammar_score", 0),
            coherence_score=评估_data.get("coherence_score", 0) or 评估_data.get("fluency_score", 0),
            transcript=transcript,
            assessment_json=json.dumps(评估_data)
        )
        db.add(assessment)
        db.flush()  # 获取assessment.id
        
        # 创建反馈条目
        strengths = 评估_data.get("strengths", [])
        weaknesses = 评估_data.get("weaknesses", [])
        suggestions = 评估_data.get("suggestions", [])
        
        # 添加优点反馈
        for strength in strengths:
            feedback = FeedbackItem(
                assessment_id=assessment.id,
                category="strength",
                description=strength,
                suggestion="继续保持",
                severity="positive"
            )
            db.add(feedback)
        
        # 添加缺点反馈
        for weakness in weaknesses:
            feedback = FeedbackItem(
                assessment_id=assessment.id,
                category="weakness",
                description=weakness,
                severity="negative"
            )
            db.add(feedback)
        
        # 添加建议反馈
        for suggestion in suggestions:
            feedback = FeedbackItem(
                assessment_id=assessment.id,
                category="suggestion",
                description=suggestion,
                severity="neutral"
            )
            db.add(feedback)
        
        # 更新会话状态
        session.status = "completed"
        session.end_time = datetime.utcnow()
        if not session.duration_seconds:
            session.duration_seconds = int((session.end_time - session.start_time).total_seconds())
        
        # 更新用户学习进度
        progress = db.query(LearningProgress).filter(LearningProgress.user_id == session.user_id).first()
        if progress:
            # 更新总练习时间
            progress.total_practice_time_seconds += session.duration_seconds
            progress.total_sessions += 1
            progress.last_practice_date = datetime.utcnow()
            
            # 更新平均分（加权平均）
            current_total = progress.average_score * (progress.total_sessions - 1)
            progress.average_score = (current_total + assessment.overall_score) / progress.total_sessions
            
            # 更新各项技能进步
            # 这里简化处理，实际应用中可能需要更复杂的算法
            progress.fluency_improvement = self._calculate_improvement(
                progress.fluency_improvement, assessment.fluency_score
            )
            progress.pronunciation_improvement = self._calculate_improvement(
                progress.pronunciation_improvement, assessment.pronunciation_score
            )
            progress.vocabulary_improvement = self._calculate_improvement(
                progress.vocabulary_improvement, assessment.vocabulary_score
            )
            progress.grammar_improvement = self._calculate_improvement(
                progress.grammar_improvement, assessment.grammar_score
            )
            progress.coherence_improvement = self._calculate_improvement(
                progress.coherence_improvement, assessment.coherence_score
            )
        
        db.commit()
        
        return {
            "assessment_id": assessment.id,
            "overall_score": assessment.overall_score,
            "fluency_score": assessment.fluency_score,
            "pronunciation_score": assessment.pronunciation_score,
            "vocabulary_score": assessment.vocabulary_score,
            "grammar_score": assessment.grammar_score,
            "coherence_score": assessment.coherence_score,
            "feedback_count": len(strengths) + len(weaknesses) + len(suggestions)
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
    
    def _calculate_improvement(self, current_improvement: float, new_score: float) -> float:
        """
        计算技能进步（简化版）
        
        Args:
            current_improvement: 当前进步值
            new_score: 新评分
            
        Returns:
            float: 更新后的进步值
        """
        # 这里使用简化的算法，实际应用中可能需要更复杂的计算
        # 例如考虑历史趋势、目标分数等
        improvement_factor = 0.1  # 新评分的权重
        return current_improvement * (1 - improvement_factor) + new_score * improvement_factor


@celery_app.task(bind=True)
def evaluate_speech_response(self, transcript: str, question: str, session_id: str):
    """
    评估语音回应（旧任务名称，保持向后兼容）
    
    Args:
        self: Celery任务实例
        transcript: 转录文本
        question: 问题
        session_id: 会话ID
        
    Returns:
        Dict: 评估结果
    """
    # 这个任务是为了处理旧的任务消息
    # 由于参数不同，我们无法直接调用evaluate_speech
    # 这里返回一个错误消息，或者根据实际情况进行处理
    return {"error": "This task is deprecated. Please use evaluate_speech instead."}