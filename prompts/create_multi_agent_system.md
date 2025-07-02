# Multi-Agent Software Development System - Complete Implementation Prompt

## Project Overview

Create a Docker-based multi-agent system for collaborative software development with the following architecture:

```
├── agents/                 # Agent implementations
├── config/                 # Agent configuration files
├── database/              # SQLite database and schemas
├── docker/                # Docker configuration
├── integrations/          # Slack and GitHub integrations (future phases)
├── shared/                # Shared utilities and models
└── config.yaml           # Main configuration file
```

## Phase 1: Single Agent with API

### Core Requirements

1. **FastAPI Application** with comprehensive REST endpoints
2. **SQLAlchemy Database** with SQLite backend
3. **Single Agent Implementation** (Code Reviewer)
4. **Configuration Management** via YAML
5. **Docker Support** with health checks
6. **Complete Test Suite**

### Technology Stack

- **Python 3.11+**
- **FastAPI** for REST API
- **SQLAlchemy** for database ORM
- **Pydantic** for data validation
- **SQLite** for database
- **Docker** for containerization
- **Uvicorn** for ASGI server

### Dependencies (requirements.txt)

```txt
# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pyyaml==6.0.1
python-dotenv==1.0.0

# Database
sqlalchemy==2.0.23
alembic==1.13.1

# AI/ML
openai==1.3.7
anthropic==0.7.8

# HTTP client
httpx==0.25.2
aiohttp==3.9.1

# Async support
asyncio-mqtt==0.16.1

# Logging and monitoring
structlog==23.2.0

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
mypy==1.7.1

# Docker and deployment
gunicorn==21.2.0
```

### Configuration (config.yaml)

```yaml
# Multi-Agent Software Development System Configuration

# Global settings
app:
  name: "Multi-Agent Software Development System"
  version: "1.0.0"
  debug: true
  log_level: "INFO"

# Database configuration
database:
  type: "sqlite"
  path: "./database/agents.db"
  backup_enabled: true
  backup_interval: 3600  # seconds

# API configuration
api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  timeout: 30

# Agent configurations
agents:
  - name: "code_reviewer"
    model: "gpt-4"
    personality: "Thorough and detail-oriented code reviewer who focuses on code quality, security, and best practices"
    job_description: "Review code changes, identify potential issues, and suggest improvements"
    system_prompt: |
      You are a senior software engineer specializing in code review. Your role is to:
      - Analyze code changes for potential bugs, security issues, and performance problems
      - Suggest improvements for code quality, readability, and maintainability
      - Ensure adherence to coding standards and best practices
      - Provide constructive feedback with specific examples
      - Consider edge cases and potential failure scenarios
    goal: "Improve code quality and prevent bugs through thorough review"
    enabled: true
    memory_enabled: true
    max_context_length: 4000

# Integration settings (to be configured in later phases)
integrations:
  slack:
    enabled: false
    bot_token: ""
    app_token: ""
    channels: []
  
  github:
    enabled: false
    access_token: ""
    webhook_secret: ""
    repositories: []

# Logging configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/app.log"
  max_size: 10485760  # 10MB
  backup_count: 5
```

### Data Models

#### Pydantic Models (shared/models.py)

Create comprehensive Pydantic models for:
- `AgentConfig`: Agent configuration
- `AgentStatus`: Enum for agent states (idle, busy, error, offline)
- `MessageType`: Enum for message types (user, assistant, system, error)
- `Message`: Individual messages
- `Conversation`: Conversation tracking
- `AgentState`: Current agent state
- `TaskRequest`: Task submission
- `TaskResponse`: Task results
- `CodeReviewRequest`: Code review input
- `CodeReviewResponse`: Code review output
- `HealthCheck`: System health status

#### SQLAlchemy Models (database/models.py)

Create database models with proper relationships:
- `Agent`: Agent information and configuration
- `AgentState`: Current agent status (use `agent_metadata` instead of `metadata` to avoid SQLAlchemy conflicts)
- `Conversation`: Conversations between agents
- `Message`: Messages in conversations (use `message_metadata`)
- `Task`: Task execution history
- `Memory`: Agent memory storage (use `memory_metadata`)
- `CodeReview`: Cached code review results

**IMPORTANT**: Avoid using `metadata` as a column name in SQLAlchemy models - use `agent_metadata`, `message_metadata`, etc.

### Core Components

#### 1. Configuration Management (shared/config.py)

Create a `ConfigManager` class that:
- Loads configuration from YAML file
- Provides type-safe access to configuration
- Supports hot-reloading
- Includes validation

#### 2. Database Manager (database/manager.py)

Create a `DatabaseManager` class that:
- Handles database connections and sessions
- Provides health checks
- Supports backup and cleanup operations
- Manages table creation and migrations

#### 3. Base Agent Class (agents/base_agent.py)

Create an abstract `BaseAgent` class with:
- Agent lifecycle management
- Status tracking and updates
- Database logging
- Task processing interface
- Health check capabilities

#### 4. Generic Agent (agents/generic_agent.py)

Implement a `GenericAgent` class that:
- Inherits from `BaseAgent`
- Uses configuration to define personality and capabilities
- Provides a flexible tool system that adapts to agent personality
- Supports multiple agent types through configuration
- Handles various task types with personality-specific responses

#### 5. Agent Manager (agents/manager.py)

Create an `AgentManager` class that:
- Manages multiple agents
- Handles agent initialization and shutdown
- Provides task routing
- Supports agent restart functionality

#### 6. FastAPI Application (main.py)

Create a comprehensive FastAPI app with endpoints:

**Core Endpoints:**
- `GET /`: Root endpoint
- `GET /health`: Health check
- `GET /agents`: List all agents
- `GET /agents/{agent_name}`: Get specific agent
- `POST /agents/{agent_name}/tasks`: Submit task to agent
- `POST /tasks`: Submit task to any agent
- `POST /code-review`: Direct code review
- `POST /agents/{agent_name}/restart`: Restart agent

**Database Endpoints:**
- `GET /database/health`: Database health
- `POST /database/backup`: Create backup
- `POST /database/cleanup`: Clean old data

**System Endpoints:**
- `GET /config`: Get configuration

### API Endpoints Specification

#### Health Check
```http
GET /health
Response: HealthCheck model with system status, agent states, database status
```

#### List Agents
```http
GET /agents
Response: List[Dict[str, Any]] with agent states
```

#### Get Agent
```http
GET /agents/{agent_name}
Response: Dict[str, Any] with agent state
```

#### Submit Task
```http
POST /agents/{agent_name}/tasks
Body: TaskRequest
Response: TaskResponse
```

#### Code Review
```http
POST /code-review
Body: CodeReviewRequest
Response: CodeReviewResponse
```

### Docker Configuration

#### Dockerfile (docker/Dockerfile)
```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/database /app/logs

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]
```

#### Docker Compose (docker-compose.yml)
```yaml
version: '3.8'

services:
  multi-agent-system:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: multi-agent-system
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
      - ./config.yaml:/app/config.yaml:ro
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - agent-network

networks:
  agent-network:
    driver: bridge

volumes:
  database-data:
  logs-data:
```

### Testing

#### Test Suite (test_agent.py)
Create comprehensive tests for:
- Health check endpoint
- Agent listing
- Code review functionality
- Task submission
- Database health
- Configuration retrieval

Test should verify:
- All endpoints return correct status codes
- Response formats match expected models
- Database operations work correctly
- Agent functionality is working

### Startup Script (start.py)
Create a startup script that:
- Checks dependencies
- Validates configuration
- Creates necessary directories
- Starts the FastAPI server
- Provides helpful error messages

### Generic Agent Features

The Generic Agent should:
1. **Configuration-Driven**: Personality and capabilities defined in config
2. **Flexible Tool System**: Common tools that adapt to agent personality
3. **Personality-Specific Responses**: Different responses based on agent type
4. **Extensible**: Easy to add new agent types through configuration
5. **Consistent API**: Uniform interface across all agent types
6. **Tool Adaptation**: Tools behave differently based on agent personality
7. **Dynamic Capabilities**: Capabilities determined by configuration, not code

### Error Handling

Implement comprehensive error handling:
- Database connection errors
- Configuration loading errors
- Agent initialization failures
- Task processing errors
- API validation errors
- Graceful shutdown handling

### Logging

Implement structured logging with:
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Contextual information (agent names, task IDs)
- File rotation and size limits
- Timestamp and source tracking

### Security Considerations

- Input validation on all endpoints
- SQL injection prevention
- Rate limiting (future enhancement)
- Environment variable usage for secrets
- Non-root Docker user

### Performance Optimizations

- Database connection pooling
- Async task processing
- Response caching
- Efficient database queries
- Memory management

### File Structure

```
AgenticDeveloperOrg/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── generic_agent.py
│   └── manager.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   └── manager.py
├── shared/
│   ├── __init__.py
│   ├── models.py
│   └── config.py
├── docker/
│   └── Dockerfile
├── config.yaml
├── main.py
├── requirements.txt
├── docker-compose.yml
├── start.py
├── test_agent.py
├── .gitignore
└── README.md
```

### Success Criteria

The implementation is complete when:
1. ✅ All tests pass (6/6)
2. ✅ API responds correctly to all endpoints
3. ✅ Database operations work properly
4. ✅ Code review functionality is working
5. ✅ Docker container starts successfully
6. ✅ Health checks pass
7. ✅ Configuration management works
8. ✅ Error handling is robust

### Testing Commands

```bash
# Start the system
python start.py

# Run tests
python test_agent.py

# Docker deployment
docker-compose up -d

# Manual API testing
curl http://localhost:8000/health
curl http://localhost:8000/agents
curl -X POST http://localhost:8000/code-review \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): print(\"world\")", "language": "python"}'
```

### Future Phases

This implementation sets up the foundation for:
- **Phase 2**: Enhanced SQLite memory storage
- **Phase 3**: Slack integration
- **Phase 4**: GitHub integration
- **Phase 5**: Multi-agent communication

### Key Implementation Notes

1. **SQLAlchemy Metadata Conflict**: Use `agent_metadata`, `message_metadata`, etc. instead of `metadata` to avoid conflicts with SQLAlchemy's declarative API.

2. **Generic Agent Architecture**: Use a single `GenericAgent` class with configuration-driven personalities rather than separate classes for each agent type.

3. **Async/Await**: Use proper async/await patterns throughout the application.

4. **Type Hints**: Include comprehensive type hints for all functions and methods.

5. **Error Messages**: Provide clear, actionable error messages.

6. **Documentation**: Include docstrings for all classes and methods.

7. **Testing**: Ensure all functionality is covered by tests.

8. **Configuration**: Make the system highly configurable via YAML with agent personalities defined in config.

9. **Tool System**: Implement a flexible tool system that adapts behavior based on agent personality.

10. **Docker**: Ensure the application runs properly in containers.

This prompt provides all the necessary details to recreate the multi-agent software development system from scratch. Follow the specifications carefully, especially the SQLAlchemy metadata naming conventions and the comprehensive API endpoint requirements. 