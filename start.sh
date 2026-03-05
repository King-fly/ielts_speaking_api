#!/bin/bash
"""
启动脚本
"""

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建.env文件（如果不存在）
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example. Please update it with your configuration."
fi

# 启动Redis（如果已安装）
if command -v redis-server &> /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
else
    echo "Redis is not installed. Please install Redis for Celery to work properly."
fi

# 启动Celery worker
echo "Starting Celery worker..."
celery -A infrastructure.tasks.speech_tasks worker --loglevel=info --detach

# 启动API服务器
echo "Starting API server..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload