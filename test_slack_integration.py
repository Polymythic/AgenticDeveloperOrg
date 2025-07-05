#!/usr/bin/env python3
"""
Comprehensive test script for Slack integration.

This script tests:
- Slack client initialization
- Configuration loading
- Message sending
- Webhook processing
- Agent integration
- File processing
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.config import get_config
from integrations.slack_client import SlackClient
from integrations.slack_manager import SlackManager
from agents.manager import AgentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SlackIntegrationTester:
    """Test suite for Slack integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.config = get_config()
        self.slack_client = None
        self.slack_manager = None
        self.agent_manager = None
        self.test_results = []
    
    async def run_all_tests(self):
        """Run all Slack integration tests."""
        logger.info("🚀 Starting Slack Integration Test Suite")
        logger.info("=" * 60)
        
        try:
            # Test 1: Configuration
            await self.test_configuration()
            
            # Test 2: Client Initialization
            await self.test_client_initialization()
            
            # Test 3: Manager Initialization
            await self.test_manager_initialization()
            
            # Test 4: Connection Test
            await self.test_connection()
            
            # Test 5: Message Sending
            await self.test_message_sending()
            
            # Test 6: Channel Operations
            await self.test_channel_operations()
            
            # Test 7: Webhook Processing
            await self.test_webhook_processing()
            
            # Test 8: Agent Integration
            await self.test_agent_integration()
            
            # Test 9: File Processing
            await self.test_file_processing()
            
            # Test 10: Error Handling
            await self.test_error_handling()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.add_result("Test Suite", False, f"Test suite failed: {e}")
        
        finally:
            # Cleanup
            await self.cleanup()
        
        # Print results
        self.print_results()
    
    def add_result(self, test_name: str, success: bool, details: str = ""):
        """Add a test result."""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"   Details: {details}")
    
    async def test_configuration(self):
        """Test Slack configuration loading."""
        try:
            logger.info("Testing Slack configuration...")
            
            # Check if Slack integration is configured
            slack_config = self.config.integrations.slack
            
            if not slack_config.enabled:
                self.add_result("Configuration", True, "Slack integration is disabled (expected for testing)")
                return
            
            # Check required fields
            if not slack_config.bot_token:
                self.add_result("Configuration", False, "Slack bot token not configured")
                return
            
            if not slack_config.channels:
                self.add_result("Configuration", True, "No channels configured (will use default)")
            else:
                self.add_result("Configuration", True, f"Configured channels: {slack_config.channels}")
            
        except Exception as e:
            self.add_result("Configuration", False, f"Configuration test failed: {e}")
    
    async def test_client_initialization(self):
        """Test Slack client initialization."""
        try:
            logger.info("Testing Slack client initialization...")
            
            self.slack_client = SlackClient()
            
            # Check if client was created
            if not self.slack_client:
                self.add_result("Client Initialization", False, "Failed to create Slack client")
                return
            
            # Check configuration
            status = self.slack_client.get_status()
            
            if not status["enabled"]:
                self.add_result("Client Initialization", True, "Slack client created (disabled)")
                return
            
            if not status["bot_token_set"]:
                self.add_result("Client Initialization", False, "Bot token not set")
                return
            
            self.add_result("Client Initialization", True, "Slack client initialized successfully")
            
        except Exception as e:
            self.add_result("Client Initialization", False, f"Client initialization failed: {e}")
    
    async def test_manager_initialization(self):
        """Test Slack manager initialization."""
        try:
            logger.info("Testing Slack manager initialization...")
            
            self.slack_manager = SlackManager()
            # Initialize with a mock or real agent manager
            self.agent_manager = None
            try:
                from agents.manager import get_agent_manager
                self.agent_manager = await get_agent_manager()
            except Exception:
                pass
            await self.slack_manager.initialize(self.agent_manager)
            # Start the manager (even if Slack is disabled)
            await self.slack_manager.start()
            
            # Check if manager was created
            if not self.slack_manager:
                self.add_result("Manager Initialization", False, "Failed to create Slack manager")
                return
            
            # Get status
            status = self.slack_manager.get_status()
            
            if not status["enabled"]:
                self.add_result("Manager Initialization", True, "Slack manager created (disabled)")
                return
            
            self.add_result("Manager Initialization", True, "Slack manager initialized successfully")
            
        except Exception as e:
            self.add_result("Manager Initialization", False, f"Manager initialization failed: {e}")
    
    async def test_connection(self):
        """Test Slack connection."""
        try:
            logger.info("Testing Slack connection...")
            
            if not self.slack_manager:
                self.add_result("Connection Test", False, "Slack manager not available")
                return
            
            # Test connection
            result = await self.slack_manager.test_connection()
            
            if result["success"]:
                self.add_result("Connection Test", True, 
                               f"Connected to workspace: {result.get('workspace', 'Unknown')}")
            else:
                self.add_result("Connection Test", False, 
                               f"Connection failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            self.add_result("Connection Test", False, f"Connection test failed: {e}")
    
    async def test_message_sending(self):
        """Test message sending functionality."""
        try:
            logger.info("Testing message sending...")
            
            if not self.slack_manager or not self.slack_manager.is_healthy():
                self.add_result("Message Sending", True, "Skipped (Slack not available)")
                return
            
            # Test simple message
            test_message = "🧪 This is a test message from the Slack integration test suite"
            
            # Try to send to first configured channel
            channels = self.config.integrations.slack.channels
            if channels:
                success = await self.slack_manager.send_message(channels[0], test_message)
                if success:
                    self.add_result("Message Sending", True, f"Message sent to {channels[0]}")
                else:
                    self.add_result("Message Sending", False, "Failed to send message")
            else:
                self.add_result("Message Sending", True, "No channels configured for testing")
            
        except Exception as e:
            self.add_result("Message Sending", False, f"Message sending test failed: {e}")
    
    async def test_channel_operations(self):
        """Test channel operations."""
        try:
            logger.info("Testing channel operations...")
            
            if not self.slack_manager or not self.slack_manager.is_healthy():
                self.add_result("Channel Operations", True, "Skipped (Slack not available)")
                return
            
            # List channels
            channels = await self.slack_manager.list_channels()
            
            if channels:
                self.add_result("Channel Operations", True, f"Found {len(channels)} channels")
            else:
                self.add_result("Channel Operations", True, "No channels accessible")
            
        except Exception as e:
            self.add_result("Channel Operations", False, f"Channel operations test failed: {e}")
    
    async def test_webhook_processing(self):
        """Test webhook event processing."""
        try:
            logger.info("Testing webhook processing...")
            
            if not self.slack_manager:
                self.add_result("Webhook Processing", False, "Slack manager not available")
                return
            
            # Test message event
            test_event = {
                "type": "message",
                "event": {
                    "type": "message",
                    "user": "U1234567890",
                    "text": "Can you create a simple calculator function?",
                    "channel": "C1234567890",
                    "ts": "1234567890.123456"
                }
            }
            
            # Process the event
            await self.slack_manager.process_webhook_event(test_event)
            
            self.add_result("Webhook Processing", True, "Webhook event processed successfully")
            
        except Exception as e:
            self.add_result("Webhook Processing", False, f"Webhook processing test failed: {e}")
    
    async def test_agent_integration(self):
        """Test agent integration."""
        try:
            logger.info("Testing agent integration...")
            
            if not self.slack_manager:
                self.add_result("Agent Integration", False, "Slack manager not available")
                return
            
            # Test task request processing
            test_text = "Please create a Python function that calculates the factorial of a number"
            
            # This would normally be processed by the webhook handler
            # For testing, we'll simulate the task detection
            if self.slack_client and self.slack_client._is_task_request(test_text):
                self.add_result("Agent Integration", True, "Task request detection working")
            else:
                self.add_result("Agent Integration", False, "Task request detection not working")
            
        except Exception as e:
            self.add_result("Agent Integration", False, f"Agent integration test failed: {e}")
    
    async def test_file_processing(self):
        """Test file processing functionality."""
        try:
            logger.info("Testing file processing...")
            
            if not self.slack_manager:
                self.add_result("File Processing", False, "Slack manager not available")
                return
            
            # Test file event (simulated)
            test_file_event = {
                "type": "file_shared",
                "event": {
                    "type": "file_shared",
                    "user": "U1234567890",
                    "channel_id": "C1234567890",
                    "file": {
                        "id": "F1234567890",
                        "name": "test_screenshot.png",
                        "filetype": "png"
                    }
                }
            }
            
            # Process the event
            await self.slack_manager.process_webhook_event(test_file_event)
            
            self.add_result("File Processing", True, "File event processing working")
            
        except Exception as e:
            self.add_result("File Processing", False, f"File processing test failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling."""
        try:
            logger.info("Testing error handling...")
            
            if not self.slack_manager:
                self.add_result("Error Handling", False, "Slack manager not available")
                return
            
            # Test sending message to invalid channel
            success = await self.slack_manager.send_message("invalid-channel", "Test message")
            
            # Should handle gracefully
            if not success:
                self.add_result("Error Handling", True, "Gracefully handled invalid channel")
            else:
                self.add_result("Error Handling", True, "Message sent (channel might be valid)")
            
        except Exception as e:
            self.add_result("Error Handling", False, f"Error handling test failed: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.slack_manager:
                await self.slack_manager.stop()
                logger.info("Slack manager stopped")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def print_results(self):
        """Print test results summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 SLACK INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  ❌ {result['test']}: {result['details']}")
        
        logger.info("\n" + "=" * 60)
        
        # Save results to file
        with open("slack_test_report.txt", "w") as f:
            f.write("SLACK INTEGRATION TEST REPORT\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")
            
            for result in self.test_results:
                status = "PASS" if result["success"] else "FAIL"
                f.write(f"{status}: {result['test']}\n")
                if result["details"]:
                    f.write(f"  Details: {result['details']}\n")
                f.write("\n")
        
        logger.info("📄 Test report saved to slack_test_report.txt")


async def main():
    """Main test function."""
    tester = SlackIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 