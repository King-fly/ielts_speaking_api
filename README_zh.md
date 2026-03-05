# IELTS Speaking API

[English Version](README.md)

这是一个基于Python技术栈开发的生产级雅思口语学习工作流API，旨在帮助用户提高雅思口语水平。API采用CLEAR架构设计，提供了完整的用户管理、口语练习、AI评估和对话模拟功能。

## 功能特点

- **用户管理系统**：注册、登录、个人资料管理、学习进度追踪
- **口语练习模块**：提供丰富的雅思口语话题、语音录制和转写功能
- **AI评分反馈**：基于雅思评分标准的多维度评估，包括流利度、词汇、语法、发音和连贯性
- **AI模拟考官对话**：智能生成符合雅思考试场景的对话，根据用户回答动态调整难度和问题方向
- **学习进度分析**：可视化展示学习数据，追踪进步情况

## 技术栈

- **FastAPI**：高性能异步Web框架，用于构建RESTful API
- **SQLAlchemy**：ORM框架，用于数据库交互
- **SQLite**：轻量级数据库，用于数据存储
- **Celery**：分布式任务队列，用于处理异步任务（如语音处理、AI评估）
- **Redis**：作为Celery的消息代理和缓存
- **OpenAI API**：用于高级AI功能（如口语评估、对话生成）
- **CrewAI**：AI代理协作框架，用于实现智能对话功能
- **SpeechRecognition**：语音识别库，用于语音转文本
- **Pydantic V2**：数据验证和设置管理

## 项目结构

项目采用CLEAR架构（Clean, Layered, Extensible, Adaptive, Reusable）设计，代码组织清晰，易于维护和扩展：

```
├── api/                 # API层 - 处理HTTP请求和响应
│   ├── routes/          # API路由定义
│   ├── dependencies/    # API依赖项
│   └── main.py          # 应用入口
├── application/         # 应用层 - 业务逻辑
│   ├── services/        # 业务服务
│   ├── use_cases/       # 用例
│   └── dto/             # 数据传输对象
├── domain/              # 领域层 - 核心业务规则和实体
│   ├── models/          # 数据模型
│   ├── entities/        # 领域实体
│   └── repositories/    # 领域仓库接口
├── infrastructure/      # 基础设施层 - 外部依赖
│   ├── database/        # 数据库连接和会话管理
│   ├── external_services/ # 外部服务集成（OpenAI、语音服务等）
│   ├── tasks/           # Celery任务
│   └── repositories/    # 仓库实现
└── shared/              # 共享层 - 通用工具和配置
    ├── config/          # 应用配置
    ├── utils/           # 通用工具
    └── schemas/         # 共享模式
```

## 快速开始

### 前提条件

- Python 3.10+
- Redis（用于Celery任务队列）
- OpenAI API密钥（可选，用于AI功能）

### 安装和运行

1. 克隆项目：

```bash
git clone https://your-repository-url/ielts_speaking_api.git
cd ielts_speaking_api
```

2. 使用提供的启动脚本：

```bash
chmod +x start.sh
./start.sh
```

启动脚本会自动创建虚拟环境、安装依赖、配置环境变量、启动Redis（如果已安装）、启动Celery worker和API服务器。

3. 手动配置（可选）：

如果需要手动配置，可以按照以下步骤操作：

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，设置必要的配置项

# 启动Redis（如果已安装）
redis-server --daemonize yes

# 启动Celery worker
celery -A infrastructure.tasks.speech_tasks worker --loglevel=info

# 启动API服务器
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### API文档

启动服务器后，可以通过以下地址访问API文档：

- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`

## API端点

### 认证相关

- `POST /api/v1/auth/register`：用户注册
- `POST /api/v1/auth/login`：用户登录
- `POST /api/v1/auth/refresh`：刷新访问令牌
- `GET /api/v1/auth/me`：获取当前用户信息

### 练习相关

- `GET /api/v1/practice/topics`：获取练习话题列表
- `GET /api/v1/practice/topics/{topic_id}`：获取特定话题详情
- `POST /api/v1/practice/topics/generate`：生成新话题
- `POST /api/v1/practice/sessions`：创建练习会话
- `POST /api/v1/practice/sessions/{session_id}/recordings`：上传语音记录
- `GET /api/v1/practice/sessions/{session_id}`：获取练习会话详情
- `GET /api/v1/practice/sessions/{session_id}/assessment`：获取练习评估结果
- `GET /api/v1/practice/sessions`：获取用户的练习会话列表

### 对话相关

- `POST /api/v1/dialogue/sessions`：创建对话会话
- `GET /api/v1/dialogue/sessions/{session_id}`：获取对话会话详情
- `POST /api/v1/dialogue/sessions/{session_id}/turns`：提交用户回应
- `GET /api/v1/dialogue/sessions/{session_id}/turns`：获取对话回合列表
- `POST /api/v1/dialogue/sessions/{session_id}/end`：结束对话会话
- `GET /api/v1/dialogue/tasks/{task_id}`：获取对话生成任务状态
- `GET /api/v1/dialogue/sessions`：获取用户的对话会话列表

### 进度相关

- `GET /api/v1/progress/overview`：获取学习进度概览
- `GET /api/v1/progress/history`：获取学习历史记录
- `GET /api/v1/progress/analytics`：获取学习分析数据

## 测试

项目包含单元测试和集成测试，可以使用以下命令运行：

```bash
# 运行所有测试
pytest

# 运行特定模块的测试
pytest tests/test_user_service.py

# 运行测试并生成覆盖率报告
pytest --cov=application --cov-report=html
```

## 部署

### Docker部署

项目提供了Dockerfile和docker-compose.yml用于容器化部署：

```bash
docker-compose up -d
```

### 生产环境部署

在生产环境中部署时，建议：

1. 使用PostgreSQL或MySQL替代SQLite
2. 配置HTTPS
3. 使用Gunicorn替代Uvicorn作为WSGI服务器
4. 使用Supervisor管理进程
5. 配置适当的日志记录和监控

## 许可证

[MIT License](LICENSE)

## 贡献

欢迎提交问题报告和拉取请求！