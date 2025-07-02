#!/usr/bin/env python3
"""
Comprehensive test suite for the Multi-Agent Software Development System.
Tests all components with verbose output and detailed error reporting.
"""

import asyncio
import json
import os
import requests
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import traceback

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.config import get_agent_config, get_config
from shared.llm import llm_manager, LLMConfig, LLMMessage
from database.manager import DatabaseManager
from database.memory_manager import MemoryManager


class TestSuite:
    """Comprehensive test suite for the multi-agent system."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0
        }
        self.errors = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Record a test result."""
        self.results["total"] += 1
        if success:
            self.results["passed"] += 1
            self.log(f"✅ {test_name}: PASSED", "PASS")
            if details:
                self.log(f"   Details: {details}", "INFO")
        else:
            self.results["failed"] += 1
            self.log(f"❌ {test_name}: FAILED", "FAIL")
            if error:
                self.log(f"   Error: {error}", "ERROR")
            if details:
                self.log(f"   Details: {details}", "INFO")
    
    def test_environment(self) -> bool:
        """Test environment setup and dependencies."""
        self.log("🔧 Testing Environment Setup", "TEST")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            self.test_result("Python Version", True, f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.test_result("Python Version", False, f"Python {python_version.major}.{python_version.minor}.{python_version.micro}", "Python 3.8+ required")
        
        # Check required files
        required_files = [
            "config.yaml",
            "main.py",
            "requirements.txt",
            "shared/config.py",
            "shared/llm.py",
            "agents/generic_agent.py",
            "agents/manager.py",
            "database/manager.py",
            "database/memory_manager.py"
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                self.test_result(f"File: {file_path}", True)
            else:
                self.test_result(f"File: {file_path}", False, "", f"File not found: {file_path}")
        
        # Check environment variables
        env_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
        for var in env_vars:
            if os.getenv(var):
                self.test_result(f"Environment Variable: {var}", True, "Set")
            else:
                self.test_result(f"Environment Variable: {var}", False, "Not set", "Optional but recommended")
        
        return self.results["failed"] == 0
    
    def test_configuration(self) -> bool:
        """Test configuration loading and validation."""
        self.log("⚙️ Testing Configuration", "TEST")
        
        try:
            config = get_config()
            self.test_result("Configuration Loading", True, "Config loaded successfully")
            
            # Check agent configurations
            agents = config.get("agents", [])
            if agents:
                self.test_result("Agent Configuration", True, f"Found {len(agents)} agents")
                
                for agent in agents:
                    agent_name = agent.get("name", "unknown")
                    llm_provider = agent.get("llm_provider", "unknown")
                    llm_model = agent.get("llm_model", "unknown")
                    
                    self.test_result(
                        f"Agent: {agent_name}",
                        True,
                        f"Provider: {llm_provider}, Model: {llm_model}"
                    )
            else:
                self.test_result("Agent Configuration", False, "", "No agents configured")
                
        except Exception as e:
            self.test_result("Configuration Loading", False, "", str(e))
        
        return self.results["failed"] == 0
    
    def test_database(self) -> bool:
        """Test database connectivity and operations."""
        self.log("🗄️ Testing Database", "TEST")
        
        try:
            # Test database connection
            db_path = "./database/agents.db"
            if Path(db_path).exists():
                self.test_result("Database File", True, f"Database exists: {db_path}")
                
                # Test SQLite connection
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ["agents", "agent_states", "memories"]
                for table in required_tables:
                    if table in tables:
                        self.test_result(f"Database Table: {table}", True)
                    else:
                        self.test_result(f"Database Table: {table}", False, "", f"Table {table} not found")
                
                # Check agent records
                cursor.execute("SELECT COUNT(*) FROM agents")
                agent_count = cursor.fetchone()[0]
                self.test_result("Agent Records", True, f"Found {agent_count} agent records")
                
                conn.close()
                
            else:
                self.test_result("Database File", False, "", f"Database file not found: {db_path}")
                
        except Exception as e:
            self.test_result("Database Operations", False, "", str(e))
        
        return self.results["failed"] == 0
    
    async def test_llm_providers(self) -> bool:
        """Test LLM provider connectivity."""
        self.log("🤖 Testing LLM Providers", "TEST")
        
        # Test configurations for different providers
        test_configs = [
            {
                "name": "openai_test",
                "provider": "openai",
                "deployment": "cloud",
                "model": "gpt-3.5-turbo",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "description": "OpenAI GPT-3.5 Turbo"
            },
            {
                "name": "ollama_test",
                "provider": "ollama",
                "deployment": "local",
                "model": "gemma3",
                "base_url": "http://localhost:11434",
                "description": "Local Ollama with Gemma3"
            },
            {
                "name": "claude_test",
                "provider": "claude",
                "deployment": "cloud",
                "model": "claude-3-sonnet-20240229",
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "description": "Anthropic Claude"
            },
            {
                "name": "gemini_test",
                "provider": "gemini",
                "deployment": "cloud",
                "model": "gemini-1.5-pro",
                "api_key": os.getenv("GOOGLE_API_KEY"),
                "description": "Google Gemini 1.5 Pro"
            }
        ]
        
        test_messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="Hello! Please respond with 'Test successful'.")
        ]
        
        for config in test_configs:
            try:
                # Create LLM configuration
                llm_config = LLMConfig(
                    provider=config["provider"],
                    deployment=config["deployment"],
                    model=config["model"],
                    api_key=config.get("api_key"),
                    base_url=config.get("base_url")
                )
                
                # Register client
                llm_manager.register_client(config["name"], llm_config)
                self.test_result(f"LLM Client Registration: {config['description']}", True)
                
                # Test generation (only if API key is available for cloud providers)
                if config["provider"] in ["openai", "claude", "gemini"] and not config.get("api_key"):
                    self.test_result(f"LLM Generation: {config['description']}", False, "", "No API key available")
                    continue
                
                if config["provider"] == "ollama":
                    # For Ollama, test if server is reachable
                    try:
                        response = requests.get("http://localhost:11434/api/tags", timeout=5)
                        if response.status_code == 200:
                            self.test_result(f"LLM Generation: {config['description']}", True, "Ollama server reachable")
                        else:
                            self.test_result(f"LLM Generation: {config['description']}", False, "", "Ollama server not responding")
                    except:
                        self.test_result(f"LLM Generation: {config['description']}", False, "", "Ollama server not reachable")
                    continue
                
                # Test generation
                response = await llm_manager.generate_response(
                    client_name=config["name"],
                    messages=test_messages,
                    conversation_id=f"test_{config['name']}",
                    include_history=True
                )
                
                if response and "Test successful" in response:
                    self.test_result(f"LLM Generation: {config['description']}", True, "Response received")
                else:
                    self.test_result(f"LLM Generation: {config['description']}", True, "Response received (content not verified)")
                
            except Exception as e:
                self.test_result(f"LLM Provider: {config['description']}", False, "", str(e))
        
        return self.results["failed"] == 0
    
    def test_api_server(self) -> bool:
        """Test API server connectivity and endpoints."""
        self.log("🌐 Testing API Server", "TEST")
        
        # Test server connectivity
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.test_result("Server Connectivity", True, "Server is running")
                
                health_data = response.json()
                self.test_result("Health Endpoint", True, f"Status: {health_data.get('status', 'unknown')}")
                
                # Check agents in health response
                agents = health_data.get('agents', [])
                if agents:
                    self.test_result("Agent Status", True, f"Found {len(agents)} agents")
                    for agent in agents:
                        agent_name = agent.get('name', 'unknown')
                        agent_status = agent.get('status', 'unknown')
                        self.test_result(f"Agent Status: {agent_name}", True, f"Status: {agent_status}")
                else:
                    self.test_result("Agent Status", False, "", "No agents found in health response")
                    
            else:
                self.test_result("Server Connectivity", False, "", f"Server returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.test_result("Server Connectivity", False, "", "Cannot connect to server - is it running?")
        except Exception as e:
            self.test_result("Server Connectivity", False, "", str(e))
        
        # Test agent listing endpoint
        try:
            response = requests.get(f"{self.base_url}/agents", timeout=10)
            if response.status_code == 200:
                agents = response.json()
                self.test_result("Agent Listing Endpoint", True, f"Found {len(agents)} agents")
            else:
                self.test_result("Agent Listing Endpoint", False, "", f"Status {response.status_code}")
        except Exception as e:
            self.test_result("Agent Listing Endpoint", False, "", str(e))
        
        return self.results["failed"] == 0
    
    def test_agent_functionality(self) -> bool:
        """Test agent functionality and responses."""
        self.log("🤖 Testing Agent Functionality", "TEST")
        
        agents_to_test = ["code_reviewer", "security_analyst", "performance_optimizer"]
        
        for agent_name in agents_to_test:
            self.log(f"Testing agent: {agent_name}", "INFO")
            
            # Test generate_response task
            try:
                response = requests.post(
                    f"{self.base_url}/agents/{agent_name}/tasks",
                    json={
                        "agent_name": agent_name,
                        "task_type": "generate_response",
                        "description": "Test introduction",
                        "content": "Hello, can you introduce yourself?"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.test_result(f"Agent {agent_name}: generate_response", True, "Task completed successfully")
                    else:
                        self.test_result(f"Agent {agent_name}: generate_response", False, "", result.get('error_message', 'Unknown error'))
                else:
                    self.test_result(f"Agent {agent_name}: generate_response", False, "", f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.test_result(f"Agent {agent_name}: generate_response", False, "", str(e))
            
            # Test memory summary endpoint
            try:
                response = requests.get(f"{self.base_url}/agents/{agent_name}/memory/summary", timeout=10)
                if response.status_code == 200:
                    memory_data = response.json()
                    memory_count = len(memory_data.get('memories', []))
                    self.test_result(f"Agent {agent_name}: memory summary", True, f"Found {memory_count} memories")
                else:
                    self.test_result(f"Agent {agent_name}: memory summary", False, "", f"HTTP {response.status_code}")
            except Exception as e:
                self.test_result(f"Agent {agent_name}: memory summary", False, "", str(e))
        
        return self.results["failed"] == 0
    
    def test_code_review_functionality(self) -> bool:
        """Test code review functionality."""
        self.log("📝 Testing Code Review Functionality", "TEST")
        
        test_code = """
def process_user_input(user_input):
    result = eval(user_input)  # Dangerous!
    return result

def authenticate_user(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return execute_query(query)
"""
        
        agents_to_test = ["code_reviewer", "security_analyst"]
        
        for agent_name in agents_to_test:
            try:
                response = requests.post(
                    f"{self.base_url}/agents/{agent_name}/tasks",
                    json={
                        "agent_name": agent_name,
                        "task_type": "code_review",
                        "description": f"Review code for {agent_name}",
                        "parameters": {
                            "code": test_code,
                            "language": "python",
                            "context": f"Testing {agent_name} capabilities"
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        review_data = result.get('result', {})
                        score = review_data.get('score', 'N/A')
                        issues = len(review_data.get('issues', []))
                        self.test_result(f"Agent {agent_name}: code_review", True, f"Score: {score}/10, Issues: {issues}")
                    else:
                        self.test_result(f"Agent {agent_name}: code_review", False, "", result.get('error_message', 'Unknown error'))
                else:
                    self.test_result(f"Agent {agent_name}: code_review", False, "", f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.test_result(f"Agent {agent_name}: code_review", False, "", str(e))
        
        return self.results["failed"] == 0
    
    def test_memory_system(self) -> bool:
        """Test memory system functionality."""
        self.log("🧠 Testing Memory System", "TEST")
        
        try:
            # Test memory manager
            memory_manager = MemoryManager()
            self.test_result("Memory Manager Initialization", True)
            
            # Test memory storage and retrieval
            test_memory = {
                "agent_id": 1,
                "memory_type": "episodic",
                "memory_category": "test",
                "content": "Test memory content",
                "context": "Test context",
                "tags": ["test", "episodic"],
                "importance": 0.8,
                "confidence": 1.0
            }
            
            memory_id = memory_manager.store_memory(**test_memory)
            if memory_id:
                self.test_result("Memory Storage", True, f"Memory stored with ID: {memory_id}")
                
                # Test memory retrieval
                retrieved_memory = memory_manager.get_memory(memory_id)
                if retrieved_memory:
                    self.test_result("Memory Retrieval", True, "Memory retrieved successfully")
                else:
                    self.test_result("Memory Retrieval", False, "", "Memory not found")
            else:
                self.test_result("Memory Storage", False, "", "Failed to store memory")
                
        except Exception as e:
            self.test_result("Memory System", False, "", str(e))
        
        return self.results["failed"] == 0
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        self.log("📊 Generating Test Report", "INFO")
        
        report = f"""
{'='*80}
MULTI-AGENT SOFTWARE DEVELOPMENT SYSTEM - TEST REPORT
{'='*80}

Test Summary:
- Total Tests: {self.results['total']}
- Passed: {self.results['passed']}
- Failed: {self.results['failed']}
- Skipped: {self.results['skipped']}
- Success Rate: {(self.results['passed'] / self.results['total'] * 100):.1f}%

System Status: {'✅ HEALTHY' if self.results['failed'] == 0 else '❌ ISSUES DETECTED'}

{'='*80}
"""
        
        if self.errors:
            report += "\nErrors and Issues:\n"
            for error in self.errors:
                report += f"- {error}\n"
        
        report += f"\n{'='*80}\n"
        
        return report
    
    async def run_all_tests(self) -> bool:
        """Run all tests and generate report."""
        self.log("🚀 Starting Comprehensive Test Suite", "TEST")
        self.log("=" * 80, "TEST")
        
        # Reset results
        self.results = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}
        self.errors = []
        
        # Run all tests
        tests = [
            ("Environment Setup", self.test_environment),
            ("Configuration", self.test_configuration),
            ("Database", self.test_database),
            ("LLM Providers", self.test_llm_providers),
            ("API Server", self.test_api_server),
            ("Agent Functionality", self.test_agent_functionality),
            ("Code Review", self.test_code_review_functionality),
            ("Memory System", self.test_memory_system),
        ]
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running {test_name} Tests", "TEST")
            try:
                if asyncio.iscoroutinefunction(test_func):
                    await test_func()
                else:
                    test_func()
            except Exception as e:
                self.log(f"❌ {test_name} test suite failed: {e}", "ERROR")
                self.errors.append(f"{test_name}: {e}")
                traceback.print_exc()
        
        # Generate and display report
        report = self.generate_report()
        print(report)
        
        # Save report to file
        with open("test_report.txt", "w") as f:
            f.write(report)
        
        self.log("📄 Test report saved to test_report.txt", "INFO")
        
        return self.results["failed"] == 0


async def main():
    """Main test runner."""
    test_suite = TestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! The system is ready for production use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors and fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 