"""
Enhanced Slack integration manager for coordinating Slack operations.

This module handles:
- Slack client lifecycle management
- Integration with the main application
- Health monitoring and status reporting
- Webhook event processing
- Agent communication coordination
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from .slack_client import SlackClient
from agents.manager import AgentManager

logger = logging.getLogger(__name__)


class SlackManager:
    """Enhanced manager for Slack integration operations."""
    
    def __init__(self):
        """Initialize the Slack manager."""
        self.slack_client = SlackClient()
        self.agent_manager: Optional[AgentManager] = None
        self._running = False
        self._health_check_interval = 300  # 5 minutes
        
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
            
            # Start health check loop
            asyncio.create_task(self._health_check_loop())
            
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
    
    async def _health_check_loop(self):
        """Periodic health check loop."""
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._perform_health_check()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def _perform_health_check(self):
        """Perform a health check on the Slack integration."""
        try:
            if not self.slack_client.enabled:
                return
            
            # Check if we can still connect to Slack
            status = self.slack_client.get_status()
            if not status.get("connected", False):
                logger.warning("Slack connection lost, attempting to reconnect...")
                await self._attempt_reconnect()
                
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect to Slack."""
        try:
            if self.agent_manager:
                await self.slack_client.initialize(self.agent_manager)
                logger.info("Successfully reconnected to Slack")
            else:
                logger.error("Cannot reconnect: agent manager not available")
        except Exception as e:
            logger.error(f"Failed to reconnect to Slack: {e}")
    
    async def send_message(self, channel: str, message: str, thread_ts: Optional[str] = None, blocks: Optional[List[Dict]] = None) -> bool:
        """Send a message to a Slack channel."""
        if not self._running:
            logger.warning("Slack manager not running")
            return False
        
        return await self.slack_client.send_message(channel, message, thread_ts, blocks)
    
    async def send_message_to_all_channels(self, message: str) -> List[Dict[str, Any]]:
        """Send a message to all configured channels."""
        if not self._running:
            logger.warning("Slack manager not running")
            return []
        
        return await self.slack_client.send_message_to_all_channels(message)
    
    async def send_agent_response(self, channel: str, user: str, agent_name: str, response: Dict[str, Any], thread_ts: Optional[str] = None):
        """Send a formatted agent response to Slack."""
        if not self._running:
            logger.warning("Slack manager not running")
            return
        
        await self.slack_client.send_agent_response(channel, user, agent_name, response, thread_ts)
    
    async def process_webhook_event(self, event_data: Dict[str, Any]):
        """Process incoming webhook events."""
        if not self._running:
            logger.warning("Slack manager not running")
            return
        
        await self.slack_client.process_webhook_event(event_data)
    
    async def broadcast_agent_status(self, agent_name: str, status: str, details: Optional[str] = None):
        """Broadcast agent status to all configured channels."""
        if not self._running or not self.slack_client.enabled:
            return
        
        message = f"🤖 *{agent_name.replace('_', ' ').title()}* status: {status}"
        if details:
            message += f"\n{details}"
        
        await self.send_message_to_all_channels(message)
    
    async def notify_task_completion(self, agent_name: str, task_description: str, result: Dict[str, Any]):
        """Notify about task completion."""
        if not self._running or not self.slack_client.enabled:
            return
        
        # Find the original channel from task parameters
        source_channel = result.get("metadata", {}).get("source_channel")
        if source_channel:
            await self.send_agent_response(
                source_channel,
                result.get("metadata", {}).get("source_user", "Unknown"),
                agent_name,
                result
            )
        else:
            # Fallback to broadcasting
            message = f"✅ *{agent_name.replace('_', ' ').title()}* completed task: {task_description[:100]}..."
            await self.send_message_to_all_channels(message)
    
    async def get_channel_info(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get information about a channel."""
        if not self._running:
            return None
        
        return await self.slack_client.get_channel_info(channel)
    
    async def list_channels(self) -> List[Dict[str, Any]]:
        """List all channels the bot has access to."""
        if not self._running:
            return []
        
        return await self.slack_client.list_channels()
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the Slack manager."""
        client_status = self.slack_client.get_status()
        
        return {
            "running": self._running,
            "enabled": client_status.get("enabled", False),
            "connected": client_status.get("connected", False),
            "channels_configured": client_status.get("channels_configured", 0),
            "bot_token_set": client_status.get("bot_token_set", False),
            "webhook_url_set": client_status.get("webhook_url_set", False),
            "health_check_interval": self._health_check_interval
        }
    
    def is_healthy(self) -> bool:
        """Check if the Slack manager is healthy."""
        if not self._running:
            return False
        
        status = self.slack_client.get_status()
        return status.get("enabled", False) and status.get("connected", False)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the Slack connection and return detailed status."""
        try:
            if not self.slack_client.enabled:
                return {
                    "success": False,
                    "error": "Slack integration is disabled",
                    "details": "Enable Slack integration in configuration"
                }
            
            if not self.slack_client.web_client:
                return {
                    "success": False,
                    "error": "Slack client not initialized",
                    "details": "Check bot token configuration"
                }
            
            # Test authentication
            auth_test = await self.slack_client.web_client.auth_test()
            if not auth_test["ok"]:
                return {
                    "success": False,
                    "error": "Authentication failed",
                    "details": auth_test.get("error", "Unknown error")
                }
            
            # Test channel access
            channels = await self.list_channels()
            
            return {
                "success": True,
                "workspace": auth_test["team"],
                "bot_user": auth_test["user"],
                "channels_available": len(channels),
                "channels_configured": len(self.slack_client.channels),
                "details": "Slack connection is working properly"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "Connection test failed",
                "details": str(e)
            }
    
    async def send_system_notification(self, message: str, level: str = "info"):
        """Send a system notification to all channels."""
        if not self._running or not self.slack_client.enabled:
            return
        
        # Add emoji based on level
        level_emojis = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        emoji = level_emojis.get(level, "ℹ️")
        formatted_message = f"{emoji} *System Notification*: {message}"
        
        await self.send_message_to_all_channels(formatted_message) 