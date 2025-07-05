"""
Enhanced Slack integration client for requirements intake and agent communication.

This module handles:
- Slack webhook integration for requirements intake
- File upload processing (screenshots, documents)
- Task routing to appropriate agents
- Real-time communication with agents
- Requirements parsing and validation
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient

from shared.config import get_config
from shared.models import TaskRequest
from agents.manager import AgentManager

logger = logging.getLogger(__name__)


class SlackClient:
    """Enhanced Slack client for requirements intake and agent communication."""
    
    def __init__(self):
        """Initialize the Slack client."""
        self.config = get_config()
        self.agent_manager = None
        
        # Slack configuration
        self.bot_token = self.config.integrations.slack.bot_token
        self.webhook_url = self.config.integrations.slack.webhook_url
        self.channels = self.config.integrations.slack.channels
        self.enabled = self.config.integrations.slack.enabled
        
        # Initialize Slack web client
        self.web_client = None
        
        # Task keywords for requirements detection
        self.requirement_keywords = [
            "create", "build", "develop", "implement", "add", "new feature",
            "requirement", "specification", "user story", "task", "enhancement",
            "bug fix", "improvement", "update", "modify", "change"
        ]
        
        # Agent routing keywords
        self.agent_keywords = {
            "code_reviewer": ["review", "check", "audit", "quality", "best practices"],
            "security_analyst": ["security", "vulnerability", "secure", "authentication", "authorization"],
            "performance_optimizer": ["performance", "optimize", "speed", "efficiency", "scalability"],
            "agentic_software_developer": ["create", "build", "develop", "implement", "generate", "code"]
        }
        
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
    
    async def send_message(self, channel: str, message: str, thread_ts: Optional[str] = None, blocks: Optional[List[Dict]] = None):
        """Send a message to a Slack channel with optional rich formatting."""
        if not self.enabled or not self.web_client:
            logger.warning("Slack client not enabled or not initialized")
            return False
        
        try:
            kwargs = {
                "channel": channel,
                "text": message,
            }
            
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            
            if blocks:
                kwargs["blocks"] = blocks
            
            response = await self.web_client.chat_postMessage(**kwargs)
            
            if response["ok"]:
                logger.info(f"Message sent to {channel}")
                return True
            else:
                logger.error(f"Failed to send message to {channel}: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to {channel}: {e}")
            return False
    
    async def send_agent_response(self, channel: str, user: str, agent_name: str, response: Dict[str, Any], thread_ts: Optional[str] = None):
        """Send a formatted agent response to Slack."""
        try:
            # Create rich message blocks
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🤖 *{agent_name.replace('_', ' ').title()}* has completed your request:"
                    }
                },
                {
                    "type": "divider"
                }
            ]
            
            # Add response content
            if "response" in response:
                content = response["response"]
                if len(content) > 3000:
                    content = content[:3000] + "...\n\n*[Response truncated - see full details in the system]*"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": content
                    }
                })
            
            # Add metadata if available
            if "metadata" in response:
                metadata = response["metadata"]
                if metadata:
                    metadata_text = "\n".join([f"• {k}: {v}" for k, v in metadata.items()])
                    blocks.append({
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Details:* {metadata_text}"
                            }
                        ]
                    })
            
            # Add timestamp
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            })
            
            # Send the message
            await self.send_message(channel, f"Response from {agent_name}", thread_ts, blocks)
            
        except Exception as e:
            logger.error(f"Error sending agent response: {e}")
            # Fallback to simple message
            await self.send_message(channel, f"🤖 {agent_name}: {response.get('response', 'Task completed')}", thread_ts)
    
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
            elif event_type == "file_shared":
                await self._handle_file_shared_event(event_data)
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
            thread_ts = event.get("thread_ts")
            ts = event.get("ts")
            
            logger.info(f"Received message from {user} in {channel}: {text[:100]}...")
            
            # Check if this looks like a task request
            if self._is_task_request(text):
                await self._process_task_request(text, user, channel, thread_ts or ts)
                
        except Exception as e:
            logger.error(f"Error handling message event: {e}")
    
    async def _handle_app_mention_event(self, event_data: Dict[str, Any]):
        """Handle app mention events from webhooks."""
        try:
            event = event_data.get("event", {})
            
            text = event.get("text", "")
            user = event.get("user", "")
            channel = event.get("channel", "")
            thread_ts = event.get("thread_ts")
            ts = event.get("ts")
            
            logger.info(f"Bot mentioned by {user} in {channel}: {text}")
            
            # Extract the actual message (remove bot mention)
            message = self._extract_message_from_mention(text)
            
            # Process as a task request
            await self._process_task_request(message, user, channel, thread_ts or ts)
            
        except Exception as e:
            logger.error(f"Error handling app mention event: {e}")
    
    async def _handle_file_shared_event(self, event_data: Dict[str, Any]):
        """Handle file shared events from webhooks."""
        try:
            event = event_data.get("event", {})
            file_info = event.get("file", {})
            
            file_id = file_info.get("id")
            file_name = file_info.get("name", "")
            file_type = file_info.get("filetype", "")
            user = event.get("user", "")
            channel = event.get("channel_id", "")
            
            logger.info(f"File shared by {user} in {channel}: {file_name} ({file_type})")
            
            # Process file based on type
            if file_type in ["png", "jpg", "jpeg", "gif"]:
                await self._process_screenshot(file_id, file_name, user, channel)
            elif file_type in ["txt", "md", "json", "yaml", "yml"]:
                await self._process_document(file_id, file_name, user, channel)
            else:
                logger.info(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error handling file shared event: {e}")
    
    def _extract_message_from_mention(self, text: str) -> str:
        """Extract the actual message from a bot mention."""
        # Remove the bot mention (format: <@BOT_ID> message)
        # This is a simple regex to remove the mention
        import re
        return re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    
    def _is_task_request(self, text: str) -> bool:
        """Check if a message looks like a task request."""
        text_lower = text.lower()
        
        # Check for requirement keywords
        for keyword in self.requirement_keywords:
            if keyword in text_lower:
                return True
        
        # Check for specific patterns
        patterns = [
            r"can you (create|build|develop|implement)",
            r"i need (a|an|some)",
            r"please (create|build|develop|implement)",
            r"add (a|an|some)",
            r"new (feature|functionality|component)"
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    async def _process_task_request(self, text: str, user: str, channel: str, thread_ts: str):
        """Process a task request and route to appropriate agent."""
        try:
            # Determine the best agent for this task
            agent_name = self._determine_agent_for_task(text)
            
            # Create task request
            task_request = TaskRequest(
                agent_name=agent_name,
                task_type="generate_response",
                description=text,
                parameters={
                    "source": "slack",
                    "user": user,
                    "channel": channel,
                    "thread_ts": thread_ts
                }
            )
            
            # Send acknowledgment
            await self.send_message(
                channel, 
                f"🤖 I'll process your request with the *{agent_name.replace('_', ' ').title()}*. This may take a moment...",
                thread_ts
            )
            
            # Submit task to agent
            if self.agent_manager:
                response = await self.agent_manager.submit_task(task_request)
                
                # Send response back to Slack
                await self.send_agent_response(channel, user, agent_name, response, thread_ts)
            else:
                await self.send_message(
                    channel,
                    "❌ Sorry, the agent system is not available right now.",
                    thread_ts
                )
                
        except Exception as e:
            logger.error(f"Error processing task request: {e}")
            await self.send_message(
                channel,
                f"❌ Sorry, there was an error processing your request: {str(e)}",
                thread_ts
            )
    
    def _determine_agent_for_task(self, text: str) -> str:
        """Determine the best agent for a given task."""
        text_lower = text.lower()
        
        # Check agent-specific keywords
        for agent_name, keywords in self.agent_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return agent_name
        
        # Default to agentic_software_developer for general requests
        return "agentic_software_developer"
    
    async def _process_screenshot(self, file_id: str, file_name: str, user: str, channel: str):
        """Process a screenshot file."""
        try:
            # Get file info
            file_info = await self.web_client.files_info(file=file_id)
            if not file_info["ok"]:
                logger.error(f"Failed to get file info: {file_info.get('error')}")
                return
            
            file_data = file_info["file"]
            file_url = file_data.get("url_private")
            
            # Create task for requirements analysis
            task_request = TaskRequest(
                agent_name="agentic_software_developer",
                task_type="generate_response",
                description=f"Analyze this screenshot and extract requirements: {file_name}",
                parameters={
                    "source": "slack",
                    "user": user,
                    "channel": channel,
                    "file_url": file_url,
                    "file_name": file_name,
                    "file_type": "screenshot"
                }
            )
            
            # Send acknowledgment
            await self.send_message(
                channel,
                f"📸 I'll analyze the screenshot *{file_name}* and extract requirements...",
                None
            )
            
            # Submit task to agent
            if self.agent_manager:
                response = await self.agent_manager.submit_task(task_request)
                await self.send_agent_response(channel, user, "agentic_software_developer", response)
            else:
                await self.send_message(
                    channel,
                    "❌ Sorry, the agent system is not available right now.",
                    None
                )
                
        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")
            await self.send_message(
                channel,
                f"❌ Sorry, there was an error processing the screenshot: {str(e)}",
                None
            )
    
    async def _process_document(self, file_id: str, file_name: str, user: str, channel: str):
        """Process a document file."""
        try:
            # Get file content
            file_info = await self.web_client.files_info(file=file_id)
            if not file_info["ok"]:
                logger.error(f"Failed to get file info: {file_info.get('error')}")
                return
            
            file_data = file_info["file"]
            file_url = file_data.get("url_private")
            
            # Create task for document analysis
            task_request = TaskRequest(
                agent_name="agentic_software_developer",
                task_type="generate_response",
                description=f"Analyze this document and extract requirements: {file_name}",
                parameters={
                    "source": "slack",
                    "user": user,
                    "channel": channel,
                    "file_url": file_url,
                    "file_name": file_name,
                    "file_type": "document"
                }
            )
            
            # Send acknowledgment
            await self.send_message(
                channel,
                f"📄 I'll analyze the document *{file_name}* and extract requirements...",
                None
            )
            
            # Submit task to agent
            if self.agent_manager:
                response = await self.agent_manager.submit_task(task_request)
                await self.send_agent_response(channel, user, "agentic_software_developer", response)
            else:
                await self.send_message(
                    channel,
                    "❌ Sorry, the agent system is not available right now.",
                    None
                )
                
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await self.send_message(
                channel,
                f"❌ Sorry, there was an error processing the document: {str(e)}",
                None
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the Slack client."""
        return {
            "enabled": self.enabled,
            "connected": self.web_client is not None,
            "channels_configured": len(self.channels),
            "bot_token_set": bool(self.bot_token),
            "webhook_url_set": bool(self.webhook_url)
        } 