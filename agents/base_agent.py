"""
Base agent class for the multi-agent system.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod

from shared.models import (
    AgentConfig, AgentStatus, Message, MessageType, 
    TaskRequest, TaskResponse, Conversation
)
from shared.config import get_agent_config
from database.manager import get_db_session
from database.models import Agent as DBAgent, AgentState as DBAgentState, Task as DBTask

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.config = get_agent_config(agent_name)
        if not self.config:
            raise ValueError(f"Agent configuration not found: {agent_name}")
        
        self.status = AgentStatus.IDLE
        self.current_task: Optional[str] = None
        self.memory_usage = 0
        self.last_activity = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}
        
        # Initialize database record
        self._init_database_record()
    
    def _init_database_record(self):
        """Initialize or update the agent's database record."""
        try:
            with get_db_session() as session:
                # Check if agent exists
                db_agent = session.query(DBAgent).filter(DBAgent.name == self.agent_name).first()
                
                if not db_agent:
                    # Create new agent record
                    db_agent = DBAgent(
                        name=self.config.name,
                        model=self.config.model,
                        personality=self.config.personality,
                        job_description=self.config.job_description,
                        system_prompt=self.config.system_prompt,
                        goal=self.config.goal,
                        enabled=self.config.enabled,
                        memory_enabled=self.config.memory_enabled,
                        max_context_length=self.config.max_context_length
                    )
                    session.add(db_agent)
                    session.commit()
                    session.refresh(db_agent)
                
                # Update or create agent state
                db_state = session.query(DBAgentState).filter(
                    DBAgentState.agent_id == db_agent.id
                ).first()
                
                if not db_state:
                    db_state = DBAgentState(
                        agent_id=db_agent.id,
                        status=self.status.value,
                        current_task=self.current_task,
                        memory_usage=self.memory_usage,
                        last_activity=self.last_activity,
                        agent_metadata=self.metadata
                    )
                    session.add(db_state)
                else:
                    db_state.status = self.status.value
                    db_state.current_task = self.current_task
                    db_state.memory_usage = self.memory_usage
                    db_state.last_activity = self.last_activity
                    db_state.agent_metadata = self.metadata
                
                session.commit()
                logger.info(f"Agent {self.agent_name} database record initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize database record for {self.agent_name}: {e}")
    
    def update_status(self, status: AgentStatus, task: Optional[str] = None):
        """Update agent status and current task."""
        self.status = status
        self.current_task = task
        self.last_activity = datetime.utcnow()
        
        try:
            with get_db_session() as session:
                db_agent = session.query(DBAgent).filter(DBAgent.name == self.agent_name).first()
                if db_agent:
                    db_state = session.query(DBAgentState).filter(
                        DBAgentState.agent_id == db_agent.id
                    ).first()
                    
                    if db_state:
                        db_state.status = status.value
                        db_state.current_task = task
                        db_state.last_activity = self.last_activity
                        session.commit()
                        
        except Exception as e:
            logger.error(f"Failed to update status for {self.agent_name}: {e}")
    
    def log_message(self, message_type: MessageType, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a message to the database."""
        try:
            with get_db_session() as session:
                db_agent = session.query(DBAgent).filter(DBAgent.name == self.agent_name).first()
                if db_agent:
                    from database.models import Message as DBMessage
                    
                    db_message = DBMessage(
                        agent_id=db_agent.id,
                        message_type=message_type.value,
                        content=content,
                        timestamp=datetime.utcnow(),
                        message_metadata=metadata
                    )
                    session.add(db_message)
                    session.commit()
                    
        except Exception as e:
            logger.error(f"Failed to log message for {self.agent_name}: {e}")
    
    def log_task(self, task_request: TaskRequest, task_response: TaskResponse):
        """Log a task to the database."""
        try:
            with get_db_session() as session:
                db_agent = session.query(DBAgent).filter(DBAgent.name == self.agent_name).first()
                if db_agent:
                    db_task = DBTask(
                        task_id=task_response.task_id,
                        agent_id=db_agent.id,
                        task_type=task_request.task_type,
                        description=task_request.description,
                        priority=task_request.priority,
                        parameters=task_request.parameters,
                        status="completed" if task_response.success else "failed",
                        result=task_response.result,
                        error_message=task_response.error_message,
                        execution_time=task_response.execution_time,
                        created_at=task_request.created_at,
                        completed_at=task_response.completed_at
                    )
                    session.add(db_task)
                    session.commit()
                    
        except Exception as e:
            logger.error(f"Failed to log task for {self.agent_name}: {e}")
    
    @abstractmethod
    async def process_task(self, task_request: TaskRequest) -> TaskResponse:
        """Process a task request and return a response."""
        pass
    
    @abstractmethod
    async def generate_response(self, input_text: str, context: Optional[str] = None) -> str:
        """Generate a response based on input text and optional context."""
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the agent."""
        return {
            "name": self.agent_name,
            "status": self.status.value,
            "current_task": self.current_task,
            "memory_usage": self.memory_usage,
            "last_activity": self.last_activity.isoformat(),
            "agent_metadata": self.metadata,
            "config": {
                "model": self.config.model,
                "personality": self.config.personality,
                "goal": self.config.goal
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the agent."""
        try:
            # Test basic functionality
            test_response = await self.generate_response("Hello, this is a health check.")
            
            return {
                "status": "healthy",
                "agent_name": self.agent_name,
                "current_status": self.status.value,
                "test_response_length": len(test_response),
                "last_activity": self.last_activity.isoformat(),
                "memory_usage": self.memory_usage
            }
            
        except Exception as e:
            logger.error(f"Health check failed for {self.agent_name}: {e}")
            return {
                "status": "unhealthy",
                "agent_name": self.agent_name,
                "error": str(e),
                "current_status": self.status.value
            } 