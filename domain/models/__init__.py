"""
领域模型包
"""
from .user import User, UserProfile
from .practice import PracticeTopic, PracticeSession, SpeechRecording, Assessment, FeedbackItem
from .dialogue import DialogueSession, DialogueTurn
from .progress import LearningProgress

__all__ = [
    "User", "UserProfile",
    "PracticeTopic", "PracticeSession", "SpeechRecording", "Assessment", "FeedbackItem",
    "DialogueSession", "DialogueTurn",
    "LearningProgress"
]