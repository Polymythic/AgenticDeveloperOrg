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

### 🤖 Current Agent Ecosystem

#### **Code Reviewer** 🔍
- **Personality**: Thorough and detail-oriented code reviewer
- **Focus**: Code quality, security, and best practices
- **LLM**: OpenAI GPT-4
- **Responsibilities**:
  - Analyze code for bugs and issues
  - Suggest improvements for readability
  - Ensure coding standards compliance
  - Provide constructive feedback

#### **Security Analyst** 🔒
- **Personality**: Security-focused vulnerability specialist
- **Focus**: Security vulnerabilities and best practices
- **LLM**: Ollama Gemma3 (local)
- **Responsibilities**:
  - Identify security vulnerabilities
  - Analyze authentication mechanisms
  - Check for common security flaws
  - Recommend security hardening

#### **Performance Optimizer** ⚡
- **Personality**: Performance optimization specialist
- **Focus**: Code efficiency and scalability
- **LLM**: Claude Haiku
- **Responsibilities**:
  - Analyze performance bottlenecks
  - Suggest optimization strategies
  - Review resource usage
  - Provide scalability recommendations

#### **Agentic Software Developer** 💻
- **Personality**: Creative and efficient software developer
- **Focus**: Code generation from requirements and specifications
- **LLM**: OpenAI GPT-4
- **Responsibilities**:
  - Generate high-quality, production-ready code
  - Follow best practices and naming conventions
  - Implement proper error handling and documentation
  - Create comprehensive unit tests
  - Provide clear comments and modular design

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
- **Code Generation**: Specialized agent for generating high-quality code from requirements
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
  - name: "agentic_software_developer"
    personality: "Creative and efficient software developer who specializes in generating high-quality code from requirements and specifications"
    job_description: "Generate code from requirements, specifications, and user stories with a focus on best practices and maintainability"
    goal: "Generate high-quality, maintainable code that meets requirements and follows best practices"
    memory_enabled: true
    max_context_length: 4000
    # LLM Configuration
    llm_provider: "openai"  # ollama, openai, claude, gemini
    llm_deployment: "cloud"  # local, cloud
    llm_model: "gpt-4"  # Specific model name
    # llm_api_key: ""  # Set via environment variable OPENAI_API_KEY
    # llm_base_url: ""  # Custom base URL (e.g., for local Ollama)
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
```

## API Endpoints

### Core Endpoints
- `GET /health` - System health check
- `GET /agents` - List all agents
- `GET /agents/{agent_name}` - Get specific agent details
- `POST /agents/{agent_name}/tasks` - Submit task to specific agent
- `POST /tasks` - Submit task to any available agent
- `POST /code-review` - Submit code for review

### Agent-Specific Endpoints
- `GET /agents/{agent_name}/memory/summary` - Get agent memory summary
- `POST /agents/{agent_name}/restart` - Restart specific agent

### Integration Endpoints
- `GET /integrations/slack/status` - Slack integration status
- `POST /integrations/slack/send` - Send Slack message

## Testing

The system includes a comprehensive test suite that validates all components:

```bash
python test_suite.py
```

**Current Test Results:**
- **Total Tests**: 50
- **Passed**: 50 ✅
- **Failed**: 0 ✅
- **Skipped**: 1 (Gemini quota limit)
- **Success Rate**: 100% ✅

## Development Status

### ✅ Completed Phases
- **Phase 1**: Foundation - Generic agent architecture, API, database, Docker
- **Phase 2**: Enhanced Memory - Hierarchical memory, multi-provider LLM support

### 🔄 Current Phase (Phase 3)
- **Agentic Software Developer**: ✅ Complete - Code generation from requirements
- **Slack Integration**: 🔄 In Progress - Requirements intake and communication
- **GitHub Integration**: ❌ Planned - Repository management and issue creation
- **Workflow Orchestration**: ❌ Planned - Task coordination and state management

### 🎯 Next Steps
1. Complete Slack integration for requirements intake
2. Implement GitHub integration for repository management
3. Build workflow orchestration engine
4. Add new agent types (Requirements Analyst, Test Generator, Documentation Writer)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 