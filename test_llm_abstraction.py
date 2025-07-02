#!/usr/bin/env python3
"""
Test script for LLM abstraction layer.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.llm import llm_manager, LLMConfig, LLMMessage
from shared.config import get_agent_config


async def test_llm_abstraction():
    """Test the LLM abstraction with different providers."""
    print("🧪 Testing LLM Abstraction Layer")
    print("=" * 50)
    
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
            "model": "llama2",
            "base_url": "http://localhost:11434",
            "description": "Local Ollama with Llama2"
        },
        {
            "name": "claude_test",
            "provider": "claude",
            "deployment": "cloud",
            "model": "claude-3-sonnet-20240229",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "description": "Anthropic Claude"
        }
    ]
    
    test_messages = [
        LLMMessage(role="system", content="You are a helpful assistant."),
        LLMMessage(role="user", content="Hello! Please respond with a short greeting.")
    ]
    
    for config in test_configs:
        print(f"\n🔍 Testing {config['description']}")
        print(f"   Provider: {config['provider']}")
        print(f"   Model: {config['model']}")
        
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
            print(f"   ✅ Client registered successfully")
            
            # Test generation (only if API key is available for cloud providers)
            if config["provider"] in ["openai", "claude"] and not config.get("api_key"):
                print(f"   ⚠️  Skipping generation test (no API key)")
                continue
            
            if config["provider"] == "ollama":
                # For Ollama, we'll just test the client creation
                print(f"   ✅ Ollama client ready (requires local Ollama server)")
                continue
            
            # Test generation
            response = await llm_manager.generate_response(
                client_name=config["name"],
                messages=test_messages,
                conversation_id=f"test_{config['name']}",
                include_history=True
            )
            
            print(f"   ✅ Generation successful")
            print(f"   📝 Response: {response[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    print(f"\n🎉 LLM abstraction test completed!")


async def test_agent_llm_integration():
    """Test LLM integration with agent configuration."""
    print(f"\n🧪 Testing Agent LLM Integration")
    print("=" * 50)
    
    try:
        # Get agent configuration
        agent_config = get_agent_config("code_reviewer")
        if not agent_config:
            print("❌ Agent configuration not found")
            return
        
        print(f"Agent: {agent_config.name}")
        print(f"LLM Provider: {agent_config.llm_provider}")
        print(f"LLM Model: {agent_config.llm_model}")
        print(f"LLM Deployment: {agent_config.llm_deployment}")
        
        if agent_config.llm_api_key:
            print(f"API Key: {'*' * 10}...{agent_config.llm_api_key[-4:]}")
        else:
            print("API Key: Not set")
        
        print("✅ Agent LLM configuration loaded successfully")
        
    except Exception as e:
        print(f"❌ Agent LLM integration test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_llm_abstraction())
    asyncio.run(test_agent_llm_integration()) 