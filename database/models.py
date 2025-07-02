"""
SQLAlchemy database models for the multi-agent system.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Agent(Base):
    """Agent table for storing agent information."""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    model = Column(String(50), nullable=False)
    personality = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    goal = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    memory_enabled = Column(Boolean, default=True)
    max_context_length = Column(Integer, default=4000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    states = relationship("AgentState", back_populates="agent")
    messages = relationship("Message", back_populates="agent")
    tasks = relationship("Task", back_populates="agent")


class AgentState(Base):
    """Current state of agents."""
    __tablename__ = "agent_states"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    status = Column(String(20), nullable=False, default="idle")
    current_task = Column(String(200), nullable=True)
    memory_usage = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    agent_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="states")


class Conversation(Base):
    """Conversations between agents or with users."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    participants = Column(JSON, nullable=False)  # List of agent names
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    conversation_metadata = Column(JSON, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Messages in conversations."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    message_type = Column(String(20), nullable=False)  # user, assistant, system, error
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")


class Task(Base):
    """Tasks performed by agents."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    task_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Integer, default=1)
    parameters = Column(JSON, nullable=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")


class Memory(Base):
    """Agent memory storage."""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    memory_type = Column(String(50), nullable=False)  # conversation, task, knowledge
    content = Column(Text, nullable=False)
    importance = Column(Float, default=1.0)  # 0.0 to 1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    accessed_at = Column(DateTime, default=datetime.utcnow)
    memory_metadata = Column(JSON, nullable=True)
    
    # Relationships
    agent = relationship("Agent")


class CodeReview(Base):
    """Code review records."""
    __tablename__ = "code_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    code_hash = Column(String(64), index=True, nullable=False)
    language = Column(String(20), nullable=False)
    review = Column(Text, nullable=False)
    suggestions = Column(JSON, nullable=True)  # List of suggestions
    issues = Column(JSON, nullable=True)  # List of issues
    score = Column(Float, nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent") 