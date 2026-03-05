"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from shared.config.settings import get_settings

settings = get_settings()

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 获取Base类
Base = declarative_base()


# 依赖项：获取数据库会话
def get_db() -> Session:
    """
    获取数据库会话的依赖项
    
    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    # 导入所有模型，确保它们被注册到Base的metadata中
    from domain.models import user, practice, dialogue, progress
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)