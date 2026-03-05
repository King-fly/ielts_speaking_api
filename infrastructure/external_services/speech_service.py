"""
语音处理服务
"""
import os
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

class SpeechService:
    """语音处理服务封装"""
    
    def __init__(self):
        """初始化语音服务"""
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300  # 调整麦克风灵敏度
        self.recognizer.dynamic_energy_threshold = True
    
    def transcribe_audio_file(self, file_path: str, language: str = "en-US") -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        转录音频文件为文本
        
        Args:
            file_path: 音频文件路径
            language: 音频语言代码，默认为英语（美国）
            
        Returns:
            Tuple: (转录文本, 元数据)，如果转录失败则返回(None, 错误信息)
        """
        if not os.path.exists(file_path):
            return None, {"error": "Audio file not found"}
        
        try:
            # 获取音频文件信息
            audio = AudioSegment.from_file(file_path)
            duration_seconds = len(audio) / 1000.0  # 转换为秒
            file_size = os.path.getsize(file_path)
            
            # 使用SpeechRecognition进行转录
            with sr.AudioFile(file_path) as source:
                audio_data = self.recognizer.record(source)
                transcript = self.recognizer.recognize_google(audio_data, language=language)
            
            metadata = {
                "duration_seconds": duration_seconds,
                "file_size_bytes": file_size,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "format": audio.format,
                "transcription_timestamp": datetime.utcnow().isoformat()
            }
            
            return transcript, metadata
            
        except sr.UnknownValueError:
            return None, {"error": "Google Speech Recognition could not understand audio"}
        except sr.RequestError as e:
            return None, {"error": f"Could not request results from Google Speech Recognition service; {e}"}
        except Exception as e:
            return None, {"error": str(e)}
    
    def transcribe_audio_data(self, audio_data: bytes, format: str = "wav", language: str = "en-US") -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        转录音频数据为文本
        
        Args:
            audio_data: 音频数据字节
            format: 音频格式（wav, mp3, m4a等）
            language: 音频语言代码
            
        Returns:
            Tuple: (转录文本, 元数据)，如果转录失败则返回(None, 错误信息)
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # 转录临时文件
            transcript, metadata = self.transcribe_audio_file(temp_file_path, language)
            
            # 删除临时文件
            os.unlink(temp_file_path)
            
            return transcript, metadata
            
        except Exception as e:
            return None, {"error": str(e)}
    
    def analyze_pronunciation(self, audio_file_path: str, reference_text: str) -> Dict[str, Any]:
        """
        分析发音准确性
        
        注意：此功能需要额外的发音评估服务，这里提供一个简化版本
        
        Args:
            audio_file_path: 音频文件路径
            reference_text: 参考文本
            
        Returns:
            Dict: 发音分析结果
        """
        # 这里提供一个简化版本，实际应用中可能需要集成更专业的发音评估服务
        # 例如 Google Cloud Speech-to-Text 的发音评估功能或其他专业服务
        
        # 首先转录音频
        transcript, metadata = self.transcribe_audio_file(audio_file_path)
        
        if not transcript:
            return {"error": "Failed to transcribe audio", "details": metadata}
        
        # 简单比较转录文本与参考文本的相似度
        # 实际应用中应使用更复杂的NLP技术进行评估
        reference_words = set(reference_text.lower().split())
        transcript_words = set(transcript.lower().split())
        
        # 计算词汇匹配率
        matched_words = reference_words.intersection(transcript_words)
        vocabulary_match_rate = len(matched_words) / len(reference_words) if reference_words else 0
        
        # 计算发音准确度得分（简化版）
        pronunciation_score = vocabulary_match_rate * 9.0  # 转换为1-9分制
        
        return {
            "reference_text": reference_text,
            "transcribed_text": transcript,
            "vocabulary_match_rate": vocabulary_match_rate,
            "pronunciation_score": round(pronunciation_score, 1),
            "metadata": metadata
        }