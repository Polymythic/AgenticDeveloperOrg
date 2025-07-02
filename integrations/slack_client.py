"""
Simple Slack integration client for basic communication.

This module handles:
- Slack webhook integration
- Message sending to channels
- Basic event processing
- Integration with the agent system
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient

from shared.config import get_config
from shared.models import TaskRequest
from agents.manager import AgentManager

logger = logging.getLogger(__name__)


class SlackClient:
    """Simple Slack client for basic communication."""
    
    def __init__(self):
        """Initialize the Slack client."""
        self.config = get_config()
        self.agent_manager = None
        
        # Slack configuration
        self.bot_token = self.config.integrations.slack.get("bot_token", "")
        self.webhook_url = self.config.integrations.slack.get("webhook_url", "")
        self.channels = self.config.integrations.slack.get("channels", [])
        self.enabled = self.config.integrations.slack.get("enabled", False)
        
        # Initialize Slack web client
        self.web_client = None
        
        logger.info(f"Slack client initialized - Enabled: {self.enabled}")
    
    async def initialize(self, agent_manager: AgentManager):
        """Initialize the Slack client with agent manager."""
        if not self.enabled:
            logger.info("Slack integration is disabled")
            return
        
        if not self.bot_token:
            logger.error("Slack bot_token is required")
            return
        
        self.agent_manager = agent_manager
        
        try:
            # Initialize web client
            self.web_client = AsyncWebClient(token=self.bot_token)
            
            # Test connection
            auth_test = await self.web_client.auth_test()
            logger.info(f"Connected to Slack workspace: {auth_test['team']}")
            
            logger.info("Slack client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Slack client: {e}")
            raise
    
    async def send_message(self, channel: str, message: str, thread_ts: Optional[str] = None):
        """Send a message to a Slack channel."""
        if not self.enabled or not self.web_client:
            logger.warning("Slack client not enabled or not initialized")
            return False
        
        try:
            response = await self.web_client.chat_postMessage(
                channel=channel,
                text=message,
                thread_ts=thread_ts
            )
            
            if response["ok"]:
                logger.info(f"Message sent to {channel}")
                return True
            else:
                logger.error(f"Failed to send message to {channel}: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to {channel}: {e}")
            return False
    
    async def send_message_to_all_channels(self, message: str):
        """Send a message to all configured channels."""
        if not self.channels:
            logger.warning("No channels configured")
            return
        
        results = []
        for channel in self.channels:
            success = await self.send_message(channel, message)
            results.append({"channel": channel, "success": success})
        
        return results
    
    async def get_channel_info(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get information about a channel."""
        if not self.web_client:
            return None
        
        try:
            response = await self.web_client.conversations_info(channel=channel)
            if response["ok"]:
                return response["channel"]
            else:
                logger.error(f"Failed to get channel info: {response.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
    
    async def list_channels(self) -> List[Dict[str, Any]]:
        """List all channels the bot has access to."""
        if not self.web_client:
            return []
        
        try:
            response = await self.web_client.conversations_list()
            if response["ok"]:
                return response["channels"]
            else:
                logger.error(f"Failed to list channels: {response.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            return []
    
    async def process_webhook_event(self, event_data: Dict[str, Any]):
        """Process incoming webhook events."""
        try:
            event_type = event_data.get("type")
            
            if event_type == "message":
                await self._handle_message_event(event_data)
            elif event_type == "app_mention":
                await self._handle_app_mention_event(event_data)
            else:
                logger.debug(f"Unhandled webhook event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
    
    async def _handle_message_event(self, event_data: Dict[str, Any]):
        """Handle message events from webhooks."""
        try:
            event = event_data.get("event", {})
            
            # Skip bot messages
            if event.get("bot_id") or event.get("user") == "USLACKBOT":
                return
            
            text = event.get("text", "")
            user = event.get("user", "")
            channel = event.get("channel", "")
            
            logger.info(f"Received message from {user} in {channel}: {text[:100]}...")
            
            # Check if this looks like a task request
            if self._is_task_request(text):
                await self._process_task_request(text, user, channel)
                
        except Exception as e:
            logger.error(f"Error handling message event: {e}")
    
    async def _handle_app_mention_event(self, event_data: Dict[str, Any]):
        """Handle app mention events from webhooks."""
        try:
            event = event_data.get("event", {})
            
            text = event.get("text", "")
            user = event.get("user", "")
            channel = event.get("channel", "")
            
            logger.info(f"Bot mentioned by {user} in {channel}: {text}")
            
            # Extract the actual message (remove bot mention)
            message = self._extract_message_from_mention(text)
            
            # Process as a task request
            await self._process_task_request(message, user, channel)
            
        except Exception as e:
            logger.error(f"Error handling app mention event: {e}")
    
    def _extract_message_from_mention(self, text: str) -> str:
        """Extract the actual message from a bot mention."""
        # Remove the bot mention (format: <@BOT_ID> message)
        import re
        return re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    
    def _is_task_request(self, text: str) -> bool:
        """Check if a message looks like a task request."""
        # Simple heuristic - look for keywords that suggest a task
        task_keywords = [
            "create", "build", "implement", "add", "fix", "update", "review",
            "analyze", "optimize", "test", "deploy", "refactor", "document"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in task_keywords)
    
    async def _process_task_request(self, text: str, user: str, channel: str):
        """Process a task request from Slack."""
        try:
            if not self.agent_manager:
                logger.warning("Agent manager not available")
                return
            
            # Create a task request
            task_request = TaskRequest(
                description=text,
                priority="medium",
                source="slack",
                metadata={
                    "slack_user": user,
                    "slack_channel": channel,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Send acknowledgment
            await self.send_message(
                channel, 
                f"Processing your request: {text[:100]}...",
                thread_ts=None
            )
            
            # Submit to agent manager
            result = await self.agent_manager.submit_task(task_request)
            
            # Send result back to Slack
            if result:
                await self.send_message(
                    channel,
                    f"Task completed! Result: {result.get('summary', 'Task processed successfully')}",
                    thread_ts=None
                )
            else:
                await self.send_message(
                    channel,
                    "Task processing failed. Please try again.",
                    thread_ts=None
                )
                
        except Exception as e:
            logger.error(f"Error processing task request: {e}")
            await self.send_message(
                channel,
                f"Error processing your request: {str(e)}",
                thread_ts=None
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the Slack client."""
        return {
            "enabled": self.enabled,
            "connected": self.web_client is not None,
            "channels": self.channels,
            "bot_token_configured": bool(self.bot_token),
            "webhook_url_configured": bool(self.webhook_url)
        } 