#!/usr/bin/env python3
"""
Test script for the multi-agent system.
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Health check passed: {data['status']}")
        print(f"   Database: {data['database_status']}")
        print(f"   Agents: {len(data['agents'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_list_agents():
    """Test listing agents."""
    print("\nTesting list agents...")
    
    try:
        response = requests.get(f"{BASE_URL}/agents")
        response.raise_for_status()
        
        agents = response.json()
        print(f"✅ Found {len(agents)} agents:")
        
        for agent in agents:
            print(f"   - {agent['name']}: {agent['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ List agents failed: {e}")
        return False


def test_code_review():
    """Test code review functionality."""
    print("\nTesting code review...")
    
    test_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Test the function
result = calculate_fibonacci(10)
print(result)
"""
    
    try:
        response = requests.post(
            f"{BASE_URL}/code-review",
            json={
                "code": test_code,
                "language": "python",
                "context": "This is a simple Fibonacci function",
                "focus_areas": ["performance", "readability"]
            }
        )
        response.raise_for_status()
        
        review = response.json()
        print("✅ Code review completed:")
        print(f"   Score: {review.get('score', 'N/A')}/10")
        print(f"   Issues: {len(review.get('issues', []))}")
        print(f"   Suggestions: {len(review.get('suggestions', []))}")
        
        if review.get('issues'):
            print("   Issues found:")
            for issue in review['issues']:
                print(f"     - {issue}")
        
        return True
        
    except Exception as e:
        print(f"❌ Code review failed: {e}")
        return False


def test_agent_task():
    """Test submitting a task to a specific agent."""
    print("\nTesting agent task submission...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agents/code_reviewer/tasks",
            json={
                "agent_name": "code_reviewer",
                "task_type": "generate_response",
                "description": "Hello, can you help me review some code?",
                "parameters": {
                    "context": "User is asking for code review help"
                }
            }
        )
        response.raise_for_status()
        
        task_response = response.json()
        print("✅ Task submitted successfully:")
        print(f"   Task ID: {task_response['task_id']}")
        print(f"   Success: {task_response['success']}")
        print(f"   Execution time: {task_response['execution_time']:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Task submission failed: {e}")
        return False


def test_database_health():
    """Test database health endpoint."""
    print("\nTesting database health...")
    
    try:
        response = requests.get(f"{BASE_URL}/database/health")
        response.raise_for_status()
        
        db_health = response.json()
        print(f"✅ Database health: {db_health['status']}")
        
        if 'table_counts' in db_health:
            print("   Table counts:")
            for table, count in db_health['table_counts'].items():
                print(f"     - {table}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False


def test_configuration():
    """Test configuration endpoint."""
    print("\nTesting configuration...")
    
    try:
        response = requests.get(f"{BASE_URL}/config")
        response.raise_for_status()
        
        config = response.json()
        print("✅ Configuration retrieved:")
        print(f"   App version: {config['app']['version']}")
        print(f"   API port: {config['api']['port']}")
        print(f"   Agents configured: {len(config['agents'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration retrieval failed: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Multi-Agent System Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("List Agents", test_list_agents),
        ("Code Review", test_code_review),
        ("Agent Task", test_agent_task),
        ("Database Health", test_database_health),
        ("Configuration", test_configuration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The multi-agent system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the logs and configuration.")
    
    return passed == total


if __name__ == "__main__":
    # Wait a bit for the server to start
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if not success:
        exit(1) 