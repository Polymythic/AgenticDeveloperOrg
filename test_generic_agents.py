#!/usr/bin/env python3
"""
Test script for the generic agent system with different personalities.
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"


def test_generic_agents():
    """Test that different agents have different personalities."""
    print("🧪 Testing Generic Agent System with Different Personalities")
    print("=" * 60)
    
    # Test code review with different agents
    test_code = """
def process_user_input(user_input):
    result = eval(user_input)  # Dangerous!
    return result

def authenticate_user(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    # SQL injection vulnerability
    return execute_query(query)
"""
    
    agents_to_test = ["code_reviewer", "security_analyst", "performance_optimizer"]
    
    for agent_name in agents_to_test:
        print(f"\n🔍 Testing {agent_name}...")
        
        # Test code review
        try:
            response = requests.post(
                f"{BASE_URL}/agents/{agent_name}/tasks",
                json={
                    "agent_name": agent_name,
                    "task_type": "code_review",
                    "description": f"Review this code for {agent_name} concerns",
                    "parameters": {
                        "code": test_code,
                        "language": "python",
                        "context": f"Testing {agent_name} capabilities",
                        "focus_areas": ["security", "performance", "quality"]
                    }
                }
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ {agent_name} code review completed")
            print(f"   Score: {result.get('result', {}).get('score', 'N/A')}/10")
            print(f"   Issues: {len(result.get('result', {}).get('issues', []))}")
            print(f"   Suggestions: {len(result.get('result', {}).get('suggestions', []))}")
            
            # Show personality-specific insights
            review_text = result.get('result', {}).get('review', '')
            if agent_name == "security_analyst" and "security" in review_text.lower():
                print("   🔒 Security-focused analysis detected")
            elif agent_name == "performance_optimizer" and "performance" in review_text.lower():
                print("   ⚡ Performance-focused analysis detected")
            elif agent_name == "code_reviewer" and "quality" in review_text.lower():
                print("   📝 Quality-focused analysis detected")
                
        except Exception as e:
            print(f"❌ {agent_name} test failed: {e}")
    
    # Test general conversation with different agents
    print(f"\n💬 Testing conversation with different agents...")
    
    test_messages = [
        "Hello, can you help me with code review?",
        "What should I focus on when writing secure code?",
        "How can I improve the performance of my application?"
    ]
    
    for message in test_messages:
        print(f"\n   Message: {message}")
        
        for agent_name in agents_to_test:
            try:
                response = requests.post(
                    f"{BASE_URL}/agents/{agent_name}/tasks",
                    json={
                        "agent_name": agent_name,
                        "task_type": "generate_response",
                        "description": message,
                        "parameters": {
                            "context": "General conversation"
                        }
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get('result', '')
                
                # Truncate for display
                display_text = response_text[:100] + "..." if len(response_text) > 100 else response_text
                print(f"   {agent_name}: {display_text}")
                
            except Exception as e:
                print(f"   {agent_name}: Error - {e}")
    
    print(f"\n🎉 Generic agent system test completed!")


def test_agent_listing():
    """Test that all configured agents are listed."""
    print(f"\n📋 Testing agent listing...")
    
    try:
        response = requests.get(f"{BASE_URL}/agents")
        response.raise_for_status()
        
        agents = response.json()
        print(f"✅ Found {len(agents)} agents:")
        
        for agent in agents:
            print(f"   - {agent['name']}: {agent['status']}")
            if 'config' in agent and 'personality' in agent['config']:
                personality = agent['config']['personality']
                print(f"     Personality: {personality[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent listing failed: {e}")
        return False


def test_health_check():
    """Test system health with multiple agents."""
    print(f"\n🏥 Testing system health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        
        health = response.json()
        print(f"✅ System status: {health['status']}")
        print(f"   Database: {health['database_status']}")
        print(f"   Agents: {len(health['agents'])}")
        
        for agent in health['agents']:
            print(f"   - {agent['name']}: {agent['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """Run all generic agent tests."""
    print("🚀 Starting Generic Agent System Tests")
    print("=" * 60)
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_check),
        ("Agent Listing", test_agent_listing),
        ("Generic Agents", test_generic_agents),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The generic agent system is working correctly.")
        print("\n✨ Key Benefits of Generic Agent System:")
        print("   - Single codebase for all agent types")
        print("   - Personality defined through configuration")
        print("   - Easy to add new agent types")
        print("   - Consistent tool availability across agents")
        print("   - Flexible and maintainable architecture")
    else:
        print("⚠️  Some tests failed. Please check the logs and configuration.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 