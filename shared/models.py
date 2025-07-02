"""
Shared data models for the multi-agent system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class MessageType(str, Enum):
    """Message type enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class AgentConfig(BaseModel):
    """Configuration for an individual agent."""
    name: str
    model: str
    personality: str
    job_description: str
    system_prompt: str
    goal: str
    enabled: bool = True
    memory_enabled: bool = True
    max_context_length: int = 4000
    # LLM configuration
    llm_provider: str = "openai"  # ollama, openai, claude, gemini
    llm_deployment: str = "cloud"  # local, cloud
    llm_model: Optional[str] = None  # Specific model name (e.g., "llama2", "gpt-4", "claude-3-sonnet")
    llm_api_key: Optional[str] = None  # API key for cloud providers
    llm_base_url: Optional[str] = None  # Custom base URL (e.g., for local Ollama)


class Message(BaseModel):
    """A message in the conversation."""
    id: Optional[str] = None
    agent_name: str
    message_type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class Conversation(BaseModel):
    """A conversation between agents or with users."""
    id: Optional[str] = None
    title: str
    participants: List[str]
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class AgentState(BaseModel):
    """Current state of an agent."""
    name: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    memory_usage: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class TaskRequest(BaseModel):
    """Request to perform a task."""
    task_id: Optional[str] = None
    agent_name: str
    task_type: str
    description: str
    priority: int = 1
    parameters: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskResponse(BaseModel):
    """Response from a completed task."""
    task_id: str
    agent_name: str
    success: bool
    result: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: float
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class CodeReviewRequest(BaseModel):
    """Request for code review."""
    code: str
    language: str
    context: Optional[str] = None
    focus_areas: Optional[List[str]] = None


class CodeReviewResponse(BaseModel):
    """Response from code review."""
    review: str
    suggestions: List[str] = []
    issues: List[str] = []
    score: Optional[float] = None
    confidence: float = 1.0


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    agents: List[AgentState]
    database_status: str
    integrations: Dict[str, str]


class MemorySummaryResponse(BaseModel):
    agent_name: str
    memory_type: Optional[str] = None
    total_memories: int
    summary: str
    raw_memories: List[Dict[str, Any]] 