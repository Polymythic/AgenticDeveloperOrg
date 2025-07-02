"""
Agent manager for handling multiple agents.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_agent import BaseAgent
from .generic_agent import GenericAgent
from shared.models import AgentStatus, TaskRequest, TaskResponse
from shared.config import get_enabled_agents

logger = logging.getLogger(__name__)


class AgentManager:
    """Manager for handling multiple agents."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize all enabled agents."""
        if self._initialized:
            return
        
        try:
            enabled_agents = get_enabled_agents()
            
            for agent_config in enabled_agents:
                await self._create_agent(agent_config.name)
            
            self._initialized = True
            logger.info(f"Agent manager initialized with {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent manager: {e}")
            raise
    
    async def _create_agent(self, agent_name: str) -> BaseAgent:
        """Create and initialize an agent."""
        try:
            # All agents use the GenericAgent class with different configurations
            # The configuration determines the personality and capabilities
            agent = GenericAgent(agent_name)
            
            self.agents[agent_name] = agent
            logger.info(f"Agent '{agent_name}' created successfully with personality: {agent.config.personality}")
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent '{agent_name}': {e}")
            raise
    
    async def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        if not self._initialized:
            await self.initialize()
        
        return self.agents.get(agent_name)
    
    async def get_all_agents(self) -> List[BaseAgent]:
        """Get all agents."""
        if not self._initialized:
            await self.initialize()
        
        return list(self.agents.values())
    
    async def get_agent_states(self) -> List[Dict[str, Any]]:
        """Get the state of all agents."""
        agents = await self.get_all_agents()
        return [agent.get_state() for agent in agents]
    
    async def submit_task(self, task_request: TaskRequest) -> TaskResponse:
        """Submit a task to a specific agent."""
        agent = await self.get_agent(task_request.agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {task_request.agent_name}")
        
        return await agent.process_task(task_request)
    
    async def submit_task_to_any_agent(self, task_type: str, description: str, **kwargs) -> Optional[TaskResponse]:
        """Submit a task to any available agent that can handle it."""
        agents = await self.get_all_agents()
        
        # Find agents that are idle and can handle the task type
        available_agents = [
            agent for agent in agents
            if agent.status == AgentStatus.IDLE
        ]
        
        if not available_agents:
            raise RuntimeError("No available agents to handle the task")
        
        # For now, just pick the first available agent
        # In the future, this could be more sophisticated (load balancing, etc.)
        agent = available_agents[0]
        
        task_request = TaskRequest(
            agent_name=agent.agent_name,
            task_type=task_type,
            description=description,
            parameters=kwargs
        )
        
        return await agent.process_task(task_request)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents."""
        agents = await self.get_all_agents()
        health_results = {}
        
        for agent in agents:
            try:
                health_result = await agent.health_check()
                health_results[agent.agent_name] = health_result
            except Exception as e:
                health_results[agent.agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(agents),
            "agents": health_results
        }
    
    async def restart_agent(self, agent_name: str) -> bool:
        """Restart a specific agent."""
        try:
            # Remove the old agent
            if agent_name in self.agents:
                old_agent = self.agents[agent_name]
                # Clean up any resources if needed
                del self.agents[agent_name]
            
            # Create a new agent
            await self._create_agent(agent_name)
            
            logger.info(f"Agent '{agent_name}' restarted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart agent '{agent_name}': {e}")
            return False
    
    async def shutdown(self):
        """Shutdown all agents."""
        try:
            for agent_name, agent in self.agents.items():
                try:
                    agent.update_status(AgentStatus.OFFLINE)
                    logger.info(f"Agent '{agent_name}' shutdown")
                except Exception as e:
                    logger.error(f"Error shutting down agent '{agent_name}': {e}")
            
            self.agents.clear()
            self._initialized = False
            logger.info("Agent manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during agent manager shutdown: {e}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about all agents."""
        return {
            "total_agents": len(self.agents),
            "agent_names": list(self.agents.keys()),
            "initialized": self._initialized,
            "agent_types": {
                name: type(agent).__name__ for name, agent in self.agents.items()
            }
        }


# Global agent manager instance
agent_manager = AgentManager()


async def get_agent_manager() -> AgentManager:
    """Get the global agent manager."""
    return agent_manager


async def initialize_agents():
    """Initialize all agents."""
    manager = await get_agent_manager()
    await manager.initialize()


async def shutdown_agents():
    """Shutdown all agents."""
    manager = await get_agent_manager()
    await manager.shutdown() 