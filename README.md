# Multi-Agent Software Development System

A Docker-based multi-agent system for collaborative software development with Slack communication, SQLite state management, and GitHub integration.

## 🎯 Project Overview

This system implements a **generic agent architecture** where agent personalities and capabilities are defined through configuration rather than hardcoded classes. The system supports multiple specialized agents (Code Reviewer, Security Analyst, Performance Optimizer, etc.) that can collaborate on software development tasks.

### 🧠 Memory Storage Strategy

The system implements a **hierarchical memory architecture** with three main memory types:

#### **Working Memory (Short-term)**
- Current conversation context
- Active task information  
- Temporary data and session state

#### **Episodic Memory (Medium-term)**
- Conversation history and patterns
- Task execution history
- Interaction sequences and workflows

#### **Semantic Memory (Long-term)**
- Learned knowledge and patterns
- Code solutions and best practices
- Agent expertise and specializations
- Cross-agent shared knowledge

#### **Memory Features**
- **Importance Scoring**: Dynamic importance calculation (0.0-1.0)
- **Semantic Search**: Vector-based memory retrieval
- **Memory Relationships**: Connected memory chains
- **Selective Forgetting**: Automatic memory decay and cleanup
- **Inter-Agent Sharing**: Collaborative knowledge building
- **Context Awareness**: Memory retrieval based on current context

## Features

- **Generic Agent Architecture**: Single codebase supporting multiple agent personalities
- **Configuration-Driven**: Agent personalities defined in YAML, no code changes needed
- **Flexible Tool System**: Common tools that adapt based on agent personality
- **Memory Management**: Hierarchical memory storage with learning capabilities
- **Slack Integration**: Agents communicate and collaborate through Slack channels
- **GitHub Integration**: Agents can commit code and review PRs as separate entities
- **Docker Deployment**: Easy containerization and scaling of agents

## Architecture

```
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Abstract base class
│   ├── generic_agent.py   # Generic agent for all personalities
│   └── manager.py         # Agent lifecycle management
├── database/              # SQLite database and schemas
│   ├── models.py          # Database models
│   └── manager.py         # Database operations
├── shared/                # Shared utilities and models
│   ├── models.py          # Pydantic data models
│   └── config.py          # Configuration management
├── docker/                # Docker configuration
├── integrations/          # Slack and GitHub integrations (future)
├── prompts/               # Implementation prompts and guides
└── config.yaml           # Agent personalities and system config
```

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd AgenticDeveloperOrg
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp env.example .env
   # Edit .env and add your API keys and configuration
   ```

4. **Configure agents** (optional):
   - Edit `config.yaml` to modify agent personalities
   - Add new agents by adding configuration entries
   - No code changes needed for new agent types

5. **Start the system**:
   ```bash
   python start.py
   ```

6. **Run tests**:
   ```bash
   python test_agent.py
   python test_generic_agents.py
   ```

7. **Deploy with Docker** (optional):
   ```bash
   docker-compose up -d
   ```

8. **Monitor agents**:
   - Check API endpoints: `http://localhost:8000/docs`
   - View agent states: `GET /agents`
   - Monitor health: `GET /health`

## Configuration

Each agent is configured via `config.yaml` with:
- **name**: Agent identifier
- **model**: AI model to use (e.g., gpt-4, claude-3)
- **personality**: Agent's behavioral traits and expertise
- **job_description**: Role and responsibilities
- **system_prompt**: Core instructions and capabilities
- **goal**: Primary objective and success criteria
- **memory_enabled**: Whether agent uses memory storage
- **max_context_length**: Maximum context window size

### Example Agent Configuration
```yaml
agents:
  - name: "security_analyst"
    personality: "Security-focused analyst who specializes in identifying vulnerabilities"
    job_description: "Analyze code and systems for security vulnerabilities"
    goal: "Ensure code security and prevent security vulnerabilities"
    memory_enabled: true
    max_context_length: 4000
```

## Environment Variables

The system uses environment variables for sensitive configuration. Copy `env.example` to `.env` and configure:

### Required Variables
- `OPENAI_API_KEY` - Your OpenAI API key for GPT models
- `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude models
- `SECRET_KEY` - Secret key for security (change in production)

### Optional Variables
- `APP_DEBUG` - Enable debug mode (true/false)
- `API_PORT` - API server port (default: 8000)
- `DATABASE_PATH` - Database file path
- `SLACK_*` - Slack integration settings (Phase 3)
- `GITHUB_*` - GitHub integration settings (Phase 4)

### Example .env file
```bash
# Copy env.example to .env and fill in your values
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
SECRET_KEY=your-secret-key-change-this
APP_DEBUG=true
API_PORT=8000
```

## Agent Communication & Memory

### Communication Channels
Agents communicate through:
- **Slack channels** for real-time collaboration (Phase 3)
- **SQLite database** for state persistence and memory storage
- **GitHub** for code collaboration and version control (Phase 4)
- **Memory system** for knowledge sharing and context awareness

### Memory-Based Collaboration
- **Shared Knowledge**: Agents share learned patterns and solutions
- **Context Awareness**: Responses informed by historical interactions
- **Learning**: Agents improve over time through memory accumulation
- **Specialization**: Each agent builds expertise in their domain

## Development

- **Python 3.9+** required
- **Docker** for containerization
- **Slack API** for communication
- **GitHub API** for repository management

## Project Phases

### ✅ **Phase 1: Generic Agent System** (Complete)
- Generic agent architecture with configuration-driven personalities
- RESTful API with comprehensive endpoints
- SQLite database with proper state management
- Docker containerization with health checks
- Three agent types: Code Reviewer, Security Analyst, Performance Optimizer

### 🔄 **Phase 2: Enhanced Memory Storage** (In Progress)
- Hierarchical memory architecture (Working, Episodic, Semantic)
- Memory importance scoring and decay mechanisms
- Semantic search and memory relationships
- Inter-agent memory sharing and collaboration
- Context-aware memory retrieval

### 📋 **Phase 3: Slack Integration** (Planned)
- Real-time agent communication via Slack
- Channel-based collaboration
- Message threading and context preservation
- Agent personality expression in conversations

### 📋 **Phase 4: GitHub Integration** (Planned)
- Code repository monitoring and analysis
- Automated code reviews and suggestions
- Pull request collaboration
- Commit history analysis and learning

## API Examples

### Basic Operations
```bash
# Health check
curl http://localhost:8000/health

# List all agents
curl http://localhost:8000/agents

# Get specific agent
curl http://localhost:8000/agents/security_analyst
```

### Code Review with Different Agents
```bash
# Security-focused review
curl -X POST "http://localhost:8000/agents/security_analyst/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "security_analyst",
    "task_type": "code_review",
    "description": "Review for security vulnerabilities",
    "parameters": {
      "code": "def process_input(data): return eval(data)",
      "language": "python"
    }
  }'

# Performance-focused review
curl -X POST "http://localhost:8000/agents/performance_optimizer/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "performance_optimizer",
    "task_type": "code_review",
    "description": "Review for performance issues",
    "parameters": {
      "code": "for i in range(1000000): process(i)",
      "language": "python"
    }
  }'
```

### Conversation with Different Personalities
```bash
# Ask security analyst
curl -X POST "http://localhost:8000/agents/security_analyst/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "security_analyst",
    "task_type": "generate_response",
    "description": "What are common security vulnerabilities?",
    "parameters": {"context": "Security discussion"}
  }'

# Ask performance optimizer
curl -X POST "http://localhost:8000/agents/performance_optimizer/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "performance_optimizer",
    "task_type": "generate_response",
    "description": "How can I optimize database queries?",
    "parameters": {"context": "Performance discussion"}
  }'
``` 