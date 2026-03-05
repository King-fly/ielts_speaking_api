"""
主应用入口
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from shared.config.settings import get_settings
from api.routes import api_router
from infrastructure.database.database import init_db, get_db

settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="IELTS Speaking Practice API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 初始化数据库
    init_db()
    print("Database initialized")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to IELTS Speaking API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """健康检查"""
    try:
        # 尝试查询数据库
        result = db.execute(text("SELECT 1")).scalar()
        db_status = "healthy" if result == 1 else "unhealthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)