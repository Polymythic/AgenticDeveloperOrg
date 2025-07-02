#!/usr/bin/env python3
"""
Simple test script for Slack integration.
Tests basic message sending functionality.
"""

import asyncio
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.config import get_config
from integrations.slack_client import SlackClient
from agents.manager import AgentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_slack_integration():
    """Test the Slack integration."""
    logger.info("Starting Slack integration test...")
    
    try:
        # Get configuration
        config = get_config()
        slack_config = config.integrations.slack
        
        logger.info(f"Slack enabled: {slack_config.get('enabled', False)}")
        logger.info(f"Bot token configured: {bool(slack_config.get('bot_token', ''))}")
        logger.info(f"Channels: {slack_config.get('channels', [])}")
        
        if not slack_config.get('enabled', False):
            logger.warning("Slack integration is disabled in configuration")
            return
        
        if not slack_config.get('bot_token', ''):
            logger.error("Slack bot token not configured")
            return
        
        # Create Slack client
        slack_client = SlackClient()
        
        # Initialize with a mock agent manager
        mock_agent_manager = None  # We'll skip agent manager for this test
        await slack_client.initialize(mock_agent_manager)
        
        logger.info("Slack client initialized successfully")
        
        # Test getting channel list
        logger.info("Testing channel list...")
        channels = await slack_client.list_channels()
        logger.info(f"Found {len(channels)} channels")
        
        # Test sending a message to the first configured channel
        configured_channels = slack_config.get('channels', [])
        if configured_channels:
            test_channel = configured_channels[0]
            test_message = "🧪 This is a test message from the Agentic Developer System!"
            
            logger.info(f"Sending test message to {test_channel}...")
            success = await slack_client.send_message(test_channel, test_message)
            
            if success:
                logger.info("✅ Test message sent successfully!")
            else:
                logger.error("❌ Failed to send test message")
        else:
            logger.warning("No channels configured for testing")
        
        # Test status
        status = slack_client.get_status()
        logger.info(f"Slack client status: {status}")
        
        logger.info("✅ Slack integration test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Slack integration test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_slack_integration()) 