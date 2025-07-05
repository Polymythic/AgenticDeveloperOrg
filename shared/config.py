"""
Configuration management for the multi-agent system.
"""

import os
import yaml
from typing import List, Optional
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration."""
    name: str = "Multi-Agent Software Development System"
    version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = "sqlite"
    path: str = "./database/agents.db"
    backup_enabled: bool = True
    backup_interval: int = 3600  # seconds


class APIConfig(BaseModel):
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    timeout: int = 30


class LLMConfig(BaseModel):
    """LLM configuration for an agent."""
    llm_provider: str = "openai"  # ollama, openai, claude, gemini
    llm_deployment: str = "cloud"  # local, cloud
    llm_model: str = "gpt-4"  # Specific model name
    llm_api_key: Optional[str] = None  # Set via environment variable
    llm_base_url: Optional[str] = None  # Custom base URL (e.g., for local Ollama)


class AgentConfig(BaseModel):
    """Agent configuration."""
    name: str
    model: str
    personality: str
    job_description: str
    system_prompt: str
    goal: str
    enabled: bool = True
    memory_enabled: bool = True
    max_context_length: int = 4000
    llm_config: Optional[LLMConfig] = None


class SlackConfig(BaseModel):
    """Slack integration configuration."""
    enabled: bool = False
    bot_token: str = ""
    webhook_url: str = ""
    channels: List[str] = Field(default_factory=list)
    app_token: Optional[str] = None  # For socket mode (future use)


class GitHubConfig(BaseModel):
    """GitHub integration configuration."""
    enabled: bool = False
    access_token: str = ""
    webhook_secret: str = ""
    repositories: List[str] = Field(default_factory=list)


class IntegrationsConfig(BaseModel):
    """Integrations configuration."""
    slack: SlackConfig = SlackConfig()
    github: GitHubConfig = GitHubConfig()


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "./logs/app.log"
    max_size: int = 10485760  # 10MB
    backup_count: int = 5


class Config(BaseModel):
    """Main configuration."""
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    api: APIConfig = APIConfig()
    agents: List[AgentConfig] = Field(default_factory=list)
    integrations: IntegrationsConfig = IntegrationsConfig()
    logging: LoggingConfig = LoggingConfig()


def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    config = Config()
    
    # App configuration
    config.app.name = os.getenv("APP_NAME", config.app.name)
    config.app.version = os.getenv("APP_VERSION", config.app.version)
    config.app.debug = os.getenv("APP_DEBUG", "true").lower() == "true"
    config.app.log_level = os.getenv("APP_LOG_LEVEL", config.app.log_level)
    
    # Database configuration
    config.database.type = os.getenv("DATABASE_TYPE", config.database.type)
    config.database.path = os.getenv("DATABASE_PATH", config.database.path)
    config.database.backup_enabled = os.getenv("DATABASE_BACKUP_ENABLED", "true").lower() == "true"
    config.database.backup_interval = int(os.getenv("DATABASE_BACKUP_INTERVAL", str(config.database.backup_interval)))
    
    # API configuration
    config.api.host = os.getenv("API_HOST", config.api.host)
    config.api.port = int(os.getenv("API_PORT", str(config.api.port)))
    config.api.workers = int(os.getenv("API_WORKERS", str(config.api.workers)))
    config.api.timeout = int(os.getenv("API_TIMEOUT", str(config.api.timeout)))
    
    # Logging configuration
    config.logging.level = os.getenv("LOG_LEVEL", config.logging.level)
    config.logging.format = os.getenv("LOG_FORMAT", config.logging.format)
    config.logging.file = os.getenv("LOG_FILE", config.logging.file)
    config.logging.max_size = int(os.getenv("LOG_MAX_SIZE", str(config.logging.max_size)))
    config.logging.backup_count = int(os.getenv("LOG_BACKUP_COUNT", str(config.logging.backup_count)))
    
    # Slack integration
    config.integrations.slack.enabled = os.getenv("SLACK_ENABLED", "false").lower() == "true"
    config.integrations.slack.bot_token = os.getenv("SLACK_BOT_TOKEN", "")
    config.integrations.slack.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    config.integrations.slack.app_token = os.getenv("SLACK_APP_TOKEN", "")
    
    # Parse channels from comma-separated string
    channels_str = os.getenv("SLACK_CHANNELS", "")
    if channels_str:
        config.integrations.slack.channels = [channel.strip() for channel in channels_str.split(",") if channel.strip()]
    
    # GitHub integration
    config.integrations.github.enabled = os.getenv("GITHUB_ENABLED", "false").lower() == "true"
    config.integrations.github.access_token = os.getenv("GITHUB_ACCESS_TOKEN", "")
    config.integrations.github.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    
    # Parse repositories from comma-separated string
    repos_str = os.getenv("GITHUB_REPOSITORIES", "")
    if repos_str:
        config.integrations.github.repositories = [repo.strip() for repo in repos_str.split(",") if repo.strip()]
    
    return config


def load_config_from_yaml() -> Config:
    """Load configuration from YAML file."""
    config_path = "config.yaml"
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as file:
        yaml_data = yaml.safe_load(file)
    
    # Load base configuration from YAML
    config = Config(**yaml_data)
    
    # Override with environment variables
    env_config = load_config_from_env()
    
    # Merge configurations (environment variables take precedence)
    config.app = env_config.app
    config.database = env_config.database
    config.api = env_config.api
    config.logging = env_config.logging
    config.integrations = env_config.integrations
    
    # Process agent configurations
    for i, agent in enumerate(config.agents):
        # Set LLM configuration from environment if not specified
        if not agent.llm_config:
            agent.llm_config = LLMConfig()
        
        # Override with environment variables for default LLM settings
        default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
        default_deployment = os.getenv("DEFAULT_LLM_DEPLOYMENT", "cloud")
        default_model = os.getenv("DEFAULT_LLM_MODEL", "gpt-4")
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Set default values if not specified
        if not agent.llm_config.llm_provider:
            agent.llm_config.llm_provider = default_provider
        if not agent.llm_config.llm_deployment:
            agent.llm_config.llm_deployment = default_deployment
        if not agent.llm_config.llm_model:
            agent.llm_config.llm_model = default_model
        if agent.llm_config.llm_provider == "ollama" and not agent.llm_config.llm_base_url:
            agent.llm_config.llm_base_url = ollama_url
    
    return config


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    
    if _config is None:
        try:
            _config = load_config_from_yaml()
        except FileNotFoundError:
            # Fallback to environment-only configuration
            _config = load_config_from_env()
    
    return _config


def reload_config():
    """Reload the configuration."""
    global _config
    _config = None
    return get_config()


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment."""
    return os.getenv("OPENAI_API_KEY", "")


def get_anthropic_api_key() -> str:
    """Get Anthropic API key from environment."""
    return os.getenv("ANTHROPIC_API_KEY", "")


def get_google_api_key() -> str:
    """Get Google API key from environment."""
    return os.getenv("GOOGLE_API_KEY", "")


def get_agent_config(agent_name: str) -> Optional[AgentConfig]:
    """Get configuration for a specific agent."""
    config = get_config()
    for agent in config.agents:
        if agent.name == agent_name:
            # Set LLM configuration from environment if not specified
            if not agent.llm_config:
                agent.llm_config = LLMConfig()
            
            # Set API keys from environment if not specified
            if agent.llm_config.llm_api_key is None:
                if agent.llm_config.llm_provider == "openai":
                    agent.llm_config.llm_api_key = get_openai_api_key()
                elif agent.llm_config.llm_provider == "claude":
                    agent.llm_config.llm_api_key = get_anthropic_api_key()
                elif agent.llm_config.llm_provider == "gemini":
                    agent.llm_config.llm_api_key = get_google_api_key()
            
            return agent
    return None


def get_enabled_agents() -> List[AgentConfig]:
    """Get all enabled agents."""
    config = get_config()
    return [agent for agent in config.agents if agent.enabled] 