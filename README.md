# IELTS Speaking API

[中文版本](README_zh.md)

This is a production-grade IELTS speaking learning workflow API developed based on Python technology stack, designed to help users improve their IELTS speaking skills. The API adopts CLEAR architecture design and provides comprehensive user management, speaking practice, AI assessment, and dialogue simulation features.

## Features

- **User Management System**: Registration, login, profile management, learning progress tracking
- **Speaking Practice Module**: Rich IELTS speaking topics, voice recording and transcription functionality
- **AI Scoring and Feedback**: Multi-dimensional assessment based on IELTS scoring standards, including fluency, vocabulary, grammar, pronunciation, and coherence
- **AI Examiner Simulation**: Intelligently generates dialogues that match IELTS exam scenarios, dynamically adjusts difficulty and question direction based on user responses
- **Learning Progress Analysis**: Visual display of learning data, tracking progress

## Technology Stack

- **FastAPI**: High-performance asynchronous web framework for building RESTful APIs
- **SQLAlchemy**: ORM framework for database interaction
- **SQLite**: Lightweight database for data storage
- **Celery**: Distributed task queue for handling asynchronous tasks (such as voice processing, AI assessment)
- **Redis**: Used as Celery's message broker and cache
- **OpenAI API**: Used for advanced AI features (such as speaking assessment, dialogue generation)
- **CrewAI**: AI agent collaboration framework for implementing intelligent dialogue functionality
- **SpeechRecognition**: Speech recognition library for voice-to-text conversion
- **Pydantic V2**: Data validation and settings management

## Project Structure

The project adopts CLEAR architecture (Clean, Layered, Extensible, Adaptive, Reusable) design, with clear code organization that is easy to maintain and extend:

```
├── api/                 # API layer - handles HTTP requests and responses
│   ├── routes/          # API route definitions
│   ├── dependencies/    # API dependencies
│   └── main.py          # Application entry point
├── application/         # Application layer - business logic
│   ├── services/        # Business services
│   ├── use_cases/       # Use cases
│   └── dto/             # Data transfer objects
├── domain/              # Domain layer - core business rules and entities
│   ├── models/          # Data models
│   ├── entities/        # Domain entities
│   └── repositories/    # Domain repository interfaces
├── infrastructure/      # Infrastructure layer - external dependencies
│   ├── database/        # Database connection and session management
│   ├── external_services/ # External service integration (OpenAI, speech services, etc.)
│   ├── tasks/           # Celery tasks
│   └── repositories/    # Repository implementations
└── shared/              # Shared layer - common utilities and configuration
    ├── config/          # Application configuration
    ├── utils/           # Common utilities
    └── schemas/         # Shared schemas
```

## Quick Start

### Prerequisites

- Python 3.10+
- Redis (for Celery task queue)
- OpenAI API key (optional, for AI features)

### Installation and Running

1. Clone the project:

```bash
git clone https://your-repository-url/ielts_speaking_api.git
cd ielts_speaking_api
```

2. Use the provided startup script:

```bash
chmod +x start.sh
./start.sh
```

The startup script will automatically create a virtual environment, install dependencies, configure environment variables, start Redis (if installed), start Celery worker, and start the API server.

3. Manual configuration (optional):

If you need manual configuration, you can follow these steps:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file to set necessary configuration items

# Start Redis (if installed)
redis-server --daemonize yes

# Start Celery worker
celery -A infrastructure.tasks.speech_tasks worker --loglevel=info

# Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Documentation

After starting the server, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

- `POST /api/v1/auth/register`: User registration
- `POST /api/v1/auth/login`: User login
- `POST /api/v1/auth/refresh`: Refresh access token
- `GET /api/v1/auth/me`: Get current user information

### Practice

- `GET /api/v1/practice/topics`: Get practice topic list
- `GET /api/v1/practice/topics/{topic_id}`: Get specific topic details
- `POST /api/v1/practice/topics/generate`: Generate new topic
- `POST /api/v1/practice/sessions`: Create practice session
- `POST /api/v1/practice/sessions/{session_id}/recordings`: Upload voice recording
- `GET /api/v1/practice/sessions/{session_id}`: Get practice session details
- `GET /api/v1/practice/sessions/{session_id}/assessment`: Get practice assessment results
- `GET /api/v1/practice/sessions`: Get user's practice session list

### Dialogue

- `POST /api/v1/dialogue/sessions`: Create dialogue session
- `GET /api/v1/dialogue/sessions/{session_id}`: Get dialogue session details
- `POST /api/v1/dialogue/sessions/{session_id}/turns`: Submit user response
- `GET /api/v1/dialogue/sessions/{session_id}/turns`: Get dialogue turn list
- `POST /api/v1/dialogue/sessions/{session_id}/end`: End dialogue session
- `GET /api/v1/dialogue/tasks/{task_id}`: Get dialogue generation task status
- `GET /api/v1/dialogue/sessions`: Get user's dialogue session list

### Progress

- `GET /api/v1/progress/overview`: Get learning progress overview
- `GET /api/v1/progress/history`: Get learning history
- `GET /api/v1/progress/analytics`: Get learning analytics data

## Testing

The project includes unit tests and integration tests, which can be run using the following commands:

```bash
# Run all tests
pytest

# Run tests for specific module
pytest tests/test_user_service.py

# Run tests and generate coverage report
pytest --cov=application --cov-report=html
```

## Deployment

### Docker Deployment

The project provides Dockerfile and docker-compose.yml for containerized deployment:

```bash
docker-compose up -d
```

### Production Deployment

For production deployment, it is recommended:

1. Use PostgreSQL or MySQL instead of SQLite
2. Configure HTTPS
3. Use Gunicorn instead of Uvicorn as WSGI server
4. Use Supervisor to manage processes
5. Configure appropriate logging and monitoring

## License

[MIT License](LICENSE)

## Contribution

Welcome to submit issue reports and pull requests!