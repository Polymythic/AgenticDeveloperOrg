# Multi-Agent Software Development System

A Docker-based multi-agent system for **end-to-end software development workflow** with Slack communication, SQLite state management, and GitHub integration.

## 🎯 Project Vision

**Goal**: Enable project owners to propose new requirements and specifications in Slack (including screenshots), automatically check them into GitHub, have coding agents generate code, create human-in-the-loop code reviews, and when approved, test, commit, and update all documentation.

### 🔄 Complete Workflow Pipeline

```
Slack Requirements → GitHub Issues → Agent Collaboration → Human Review → Automated Testing → Deployment
     ↓                    ↓                    ↓                    ↓                    ↓                    ↓
1. Project owner posts  2. System creates     3. Agents coordinate 4. Human approves    5. Automated tests   6. Code deployed
   requirements +        GitHub issues from    and generate code    or requests          run and validate    and docs updated
   screenshots in        Slack messages        based on specs       changes              code quality
   Slack channel
```

## 🎯 Project Overview

This system implements a **generic agent architecture** where agent personalities and capabilities are defined through configuration rather than hardcoded classes. The system supports multiple specialized agents that collaborate on software development tasks through a complete workflow pipeline.

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

### 🧠 Memory Storage Decision Logic

The system uses a programmatic, rule-based approach to decide how and when to store agent memories:

- **Episodic Memory**: After every completed task, an episodic memory is stored summarizing the task type, description, parameters, and execution context (success/failure, timing, etc.).
- **Semantic Memory**: If a task produces a significant result (e.g., code review, suggestions, or knowledge), semantic memories are stored:
  - **Knowledge**: Key results or insights from the task (e.g., code review summary)
  - **Solution**: Any actionable suggestions or solutions generated
- **Importance Scoring**: Importance is set higher for failed tasks (episodic), and for significant knowledge or solutions (semantic). The score is currently fixed by rule, but can be made dynamic in the future.
- **Confidence**: Set to 1.0 for all stored memories by default.
- **Tags**: Each memory is tagged with the task type and relevant categories (e.g., 'code_review', 'suggestions').

#### Example Storage Flow
1. **Task completes** → Store episodic memory (task summary)
2. **If result contains review/knowledge** → Store semantic memory (knowledge)
3. **If result contains suggestions** → Store semantic memory (solution)

This logic is implemented in the agent's `_store_task_memory` method. In the future, LLM-based or more dynamic decision logic can be added for more nuanced memory management.

## Features

- **Generic Agent Architecture**: Single codebase supporting multiple agent personalities
- **Configuration-Driven**: Agent personalities defined in YAML, no code changes needed
- **Flexible Tool System**: Common tools that adapt based on agent personality
- **Multi-Provider LLM Support**: Unified interface for OpenAI, Claude, Gemini, and Ollama
- **Memory Management**: Hierarchical memory storage with learning capabilities
- **Slack Integration**: Agents communicate and collaborate through Slack channels
- **GitHub Integration**: Agents can commit code and review PRs as separate entities
- **Docker Deployment**: Easy containerization and scaling of agents
- **End-to-End Workflow**: Complete pipeline from requirements to deployment

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
├── integrations/          # Slack and GitHub integrations
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
   python test_suite.py
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
    # LLM Configuration
    llm_provider: "ollama"  # ollama, openai, claude, gemini
    llm_deployment: "local"  # local, cloud
    llm_model: "gemma3"  # Specific model name
    llm_base_url: "http://localhost:11434"  # For local Ollama
```

## Environment Variables

The system uses environment variables for sensitive configuration. Copy `env.example` to `.env` and configure:

### Required Variables
- `OPENAI_API_KEY` - Your OpenAI API key for GPT models
- `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude models
- `GOOGLE_API_KEY` - Your Google API key for Gemini models
- `SECRET_KEY` - Secret key for security (change in production)

### Optional Variables
- `APP_DEBUG` - Enable debug mode (true/false)
- `API_PORT` - API server port (default: 8000)
- `DATABASE_PATH` - Database file path
- `DEFAULT_LLM_PROVIDER` - Default LLM provider (ollama, openai, claude, gemini)
- `DEFAULT_LLM_DEPLOYMENT` - Default deployment (local, cloud)
- `DEFAULT_LLM_MODEL` - Default model name
- `OLLAMA_BASE_URL` - Ollama server URL (default: http://localhost:11434)
- `SLACK_*` - Slack integration settings (Phase 3)
- `GITHUB_*` - GitHub integration settings (Phase 4)

### Example .env file
```bash
# Copy env.example to .env and fill in your values
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here
SECRET_KEY=your-secret-key-change-this
APP_DEBUG=true
API_PORT=8000

# LLM Configuration
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_DEPLOYMENT=cloud
DEFAULT_LLM_MODEL=gpt-4
OLLAMA_BASE_URL=http://localhost:11434
```

## LLM Providers

The system supports multiple LLM providers through a unified abstraction layer:

### Supported Providers
- **OpenAI** (GPT-3.5, GPT-4) - Cloud-based, requires API key
- **Anthropic Claude** (Claude-3) - Cloud-based, requires API key  
- **Google Gemini** (Gemini Pro) - Cloud-based, requires API key
- **Ollama** (Llama2, CodeLlama, etc.) - Local deployment, no API key required

### Configuration Examples

#### OpenAI (Cloud)
```yaml
llm_provider: "openai"
llm_deployment: "cloud"
llm_model: "gpt-4"
# API key set via OPENAI_API_KEY environment variable
```

#### Ollama (Local)
```yaml
llm_provider: "ollama"
llm_deployment: "local"
llm_model: "llama2"
llm_base_url: "http://localhost:11434"
```

#### Claude (Cloud)
```yaml
llm_provider: "claude"
llm_deployment: "cloud"
llm_model: "claude-3-haiku-20240307"
# API key set via ANTHROPIC_API_KEY environment variable
```

### Features
- **Conversation History**: Automatic tracking of conversation context
- **Fallback Support**: Graceful fallback to personality-based responses if LLM fails
- **Provider Mixing**: Different agents can use different providers
- **Local/Cloud Mixing**: Some agents can use local Ollama, others cloud providers

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

### ✅ **Phase 2: Enhanced Memory Storage** (Complete)
- Hierarchical memory architecture (Working, Episodic, Semantic)
- Memory importance scoring and decay mechanisms
- Semantic search and memory relationships
- Inter-agent memory sharing and collaboration
- Context-aware memory retrieval
- Multi-provider LLM abstraction layer

### 🔄 **Phase 3: End-to-End Workflow Orchestration** (In Progress)
- **Slack Integration**: Requirements intake and file upload handling
- **Workflow Engine**: Task queue and agent coordination system
- **GitHub Integration**: Repository management and code collaboration
- **Human-in-the-Loop**: Approval gates and review processes
- **New Agent Types**: Requirements Analyst, Code Generator, Test Generator, Documentation Writer

### 📋 **Phase 4: Advanced Features** (Planned)
- **Automated Testing**: Test generation and execution
- **Deployment Pipeline**: CI/CD integration
- **Monitoring & Analytics**: Performance tracking and insights
- **Advanced Workflows**: Complex multi-step processes

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

## Test Suite and Quality Assurance

- The project includes a comprehensive test suite (`test_suite.py`) that covers environment, configuration, database, LLM providers, API endpoints, agent functionality, code review, and memory system.
- **Quota/rate limit errors (e.g., HTTP 429, quota exceeded) are treated as warnings, not errors.** These are counted as 'skipped' tests and are clearly shown as warnings in the test report.
- The test suite should be run frequently to ensure no regressions. All tests must pass (with only quota/rate limit issues as warnings) before merging or deploying.
- The test report is saved to `test_report.txt` after each run, summarizing passed, failed, skipped tests, and warnings.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `python test_suite.py`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 