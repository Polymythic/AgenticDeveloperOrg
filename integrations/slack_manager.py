"""
Slack integration manager for coordinating Slack operations.

This module handles:
- Slack client lifecycle management
- Integration with the main application
- Health monitoring and status reporting
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .slack_client import SlackClient
from agents.manager import AgentManager

logger = logging.getLogger(__name__)


class SlackManager:
    """Manager for Slack integration operations."""
    
    def __init__(self):
        """Initialize the Slack manager."""
        self.slack_client = SlackClient()
        self.agent_manager: Optional[AgentManager] = None
        self._running = False
        
        logger.info("Slack manager initialized")
    
    async def initialize(self, agent_manager: AgentManager):
        """Initialize the Slack manager with agent manager."""
        try:
            self.agent_manager = agent_manager
            await self.slack_client.initialize(agent_manager)
            logger.info("Slack manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Slack manager: {e}")
            raise
    
    async def start(self):
        """Start the Slack manager."""
        if not self.slack_client.enabled:
            logger.info("Slack integration is disabled")
            return
        
        try:
            self._running = True
            logger.info("Slack manager started")
        except Exception as e:
            logger.error(f"Failed to start Slack manager: {e}")
            raise
    
    async def stop(self):
        """Stop the Slack manager."""
        try:
            self._running = False
            logger.info("Slack manager stopped")
        except Exception as e:
            logger.error(f"Error stopping Slack manager: {e}")
    
    async def send_message(self, channel: str, message: str, thread_ts: Optional[str] = None) -> bool:
        """Send a message to a Slack channel."""
        if not self._running:
            logger.warning("Slack manager not running")
            return False
        
        return await self.slack_client.send_message(channel, message, thread_ts)
    
    async def send_message_to_all_channels(self, message: str) -> list:
        """Send a message to all configured channels."""
        if not self._running:
            logger.warning("Slack manager not running")
            return []
        
        return await self.slack_client.send_message_to_all_channels(message)
    
    async def process_webhook_event(self, event_data: Dict[str, Any]):
        """Process incoming webhook events."""
        if not self._running:
            logger.warning("Slack manager not running")
            return
        
        await self.slack_client.process_webhook_event(event_data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the Slack manager."""
        return {
            "running": self._running,
            "enabled": self.slack_client.enabled,
            "client_status": self.slack_client.get_status()
        }
    
    def is_healthy(self) -> bool:
        """Check if the Slack manager is healthy."""
        if not self._running:
            return False
        
        status = self.slack_client.get_status()
        return status.get("enabled", False) and status.get("connected", False) 