"""
用户服务
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from domain.models import User, UserProfile, LearningProgress
from shared.config.settings import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """用户服务类"""
    
    def __init__(self, db: Session):
        """初始化用户服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        验证用户身份
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            User: 验证成功返回用户对象，否则返回None
        """
        user = self.get_user_by_username(username)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量
            
        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否匹配
        """
        # Bcrypt limitation: password cannot be longer than 72 bytes
        truncated_password = plain_password[:72]
        return pwd_context.verify(truncated_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        获取密码哈希值
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希密码
        """
        # Bcrypt limitation: password cannot be longer than 72 bytes
        truncated_password = password[:72]
        return pwd_context.hash(truncated_password)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            User: 用户对象，不存在则返回None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            email: 邮箱
            
        Returns:
            User: 用户对象，不存在则返回None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        通过ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            User: 用户对象，不存在则返回None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            
        Returns:
            User: 创建的用户对象
        """
        # 创建用户
        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        self.db.add(user)
        self.db.flush()  # 获取user.id
        
        # 创建用户资料
        profile = UserProfile(user_id=user.id)
        self.db.add(profile)
        
        # 创建学习进度记录
        progress = LearningProgress(user_id=user.id)
        self.db.add(progress)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        更新用户资料
        
        Args:
            user_id: 用户ID
            profile_data: 要更新的资料数据
            
        Returns:
            UserProfile: 更新后的用户资料，不存在则返回None
        """
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return None
        
        # 更新资料字段
        for key, value in profile_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def get_user_progress(self, user_id: int) -> Optional[LearningProgress]:
        """
        获取用户学习进度
        
        Args:
            user_id: 用户ID
            
        Returns:
            LearningProgress: 用户学习进度，不存在则返回None
        """
        return self.db.query(LearningProgress).filter(LearningProgress.user_id == user_id).first()