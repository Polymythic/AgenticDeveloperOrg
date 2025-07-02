"""
Configuration management for the multi-agent system.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from pydantic import BaseModel
from dotenv import load_dotenv

from .models import AgentConfig

# Load environment variables from .env file
load_dotenv()


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = os.getenv("DATABASE_TYPE", "sqlite")
    path: str = os.getenv("DATABASE_PATH", "./database/agents.db")
    backup_enabled: bool = os.getenv("DATABASE_BACKUP_ENABLED", "true").lower() == "true"
    backup_interval: int = int(os.getenv("DATABASE_BACKUP_INTERVAL", "3600"))


class APIConfig(BaseModel):
    """API configuration."""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    workers: int = int(os.getenv("API_WORKERS", "4"))
    timeout: int = int(os.getenv("API_TIMEOUT", "30"))


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file: str = os.getenv("LOG_FILE", "./logs/app.log")
    max_size: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))
    backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))


class AppConfig(BaseModel):
    """Application configuration."""
    name: str = os.getenv("APP_NAME", "Multi-Agent Software Development System")
    version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("APP_LOG_LEVEL", "INFO")


class IntegrationConfig(BaseModel):
    """Integration configuration."""
    slack: Dict[str, Any] = {
        "enabled": os.getenv("SLACK_ENABLED", "false").lower() == "true",
        "bot_token": os.getenv("SLACK_BOT_TOKEN", ""),
        "app_token": os.getenv("SLACK_APP_TOKEN", ""),
        "channels": os.getenv("SLACK_CHANNELS", "").split(",") if os.getenv("SLACK_CHANNELS") else []
    }
    github: Dict[str, Any] = {
        "enabled": os.getenv("GITHUB_ENABLED", "false").lower() == "true",
        "access_token": os.getenv("GITHUB_ACCESS_TOKEN", ""),
        "webhook_secret": os.getenv("GITHUB_WEBHOOK_SECRET", ""),
        "repositories": os.getenv("GITHUB_REPOSITORIES", "").split(",") if os.getenv("GITHUB_REPOSITORIES") else []
    }


class AIModelConfig(BaseModel):
    """AI model configuration."""
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    default_model: str = os.getenv("DEFAULT_MODEL", "gpt-4")


class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: str = os.getenv("SECRET_KEY", "change-this-in-production")
    environment: str = os.getenv("ENVIRONMENT", "development")


class Config(BaseModel):
    """Main configuration class."""
    app: AppConfig
    database: DatabaseConfig
    api: APIConfig
    agents: List[AgentConfig]
    integrations: IntegrationConfig
    logging: LoggingConfig
    ai_models: AIModelConfig
    security: SecurityConfig


class ConfigManager:
    """Configuration manager for the multi-agent system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """Load configuration from YAML file and environment variables."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Add environment-based configurations
        config_data["ai_models"] = {}
        config_data["security"] = {}
        
        self._config = Config(**config_data)
        return self._config
    
    def get_config(self) -> Config:
        """Get the current configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent."""
        config = self.get_config()
        for agent in config.agents:
            if agent.name == agent_name:
                return agent
        return None
    
    def get_enabled_agents(self) -> List[AgentConfig]:
        """Get all enabled agents."""
        config = self.get_config()
        return [agent for agent in config.agents if agent.enabled]
    
    def reload_config(self) -> Config:
        """Reload configuration from file."""
        self._config = None
        return self.load_config()


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the global configuration."""
    return config_manager.get_config()


def get_agent_config(agent_name: str) -> Optional[AgentConfig]:
    """Get configuration for a specific agent."""
    return config_manager.get_agent_config(agent_name)


def get_enabled_agents() -> List[AgentConfig]:
    """Get all enabled agents."""
    return config_manager.get_enabled_agents()


def get_ai_model_config() -> AIModelConfig:
    """Get AI model configuration."""
    return config_manager.get_config().ai_models


def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    return config_manager.get_config().security


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment."""
    return os.getenv("OPENAI_API_KEY", "")


def get_anthropic_api_key() -> str:
    """Get Anthropic API key from environment."""
    return os.getenv("ANTHROPIC_API_KEY", "")


def validate_environment() -> Dict[str, bool]:
    """Validate that required environment variables are set."""
    validation = {
        "openai_api_key": bool(get_openai_api_key()),
        "anthropic_api_key": bool(get_anthropic_api_key()),
        "secret_key": bool(os.getenv("SECRET_KEY")),
        "environment": bool(os.getenv("ENVIRONMENT"))
    }
    return validation 