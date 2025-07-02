"""
LLM abstraction layer supporting multiple providers (Ollama, OpenAI, Claude, Gemini).
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
import aiohttp
import json

logger = logging.getLogger(__name__)

# Type definitions
LLMProvider = Literal["ollama", "openai", "claude", "gemini"]
LLMDeployment = Literal["local", "cloud"]


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: LLMProvider
    deployment: LLMDeployment
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7


@dataclass
class LLMMessage:
    """Standardized message format for LLM calls."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMClient(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def generate(
        self, 
        messages: List[LLMMessage], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    def _validate_messages(self, messages: List[LLMMessage]) -> None:
        """Validate message format."""
        if not messages:
            raise ValueError("At least one message is required")
        
        for msg in messages:
            if not isinstance(msg, LLMMessage):
                raise ValueError(f"Invalid message format: {msg}")
            if msg.role not in ["system", "user", "assistant"]:
                raise ValueError(f"Invalid role: {msg.role}")


class OllamaClient(LLMClient):
    """Ollama client for local LLM inference."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using Ollama API."""
        self._validate_messages(messages)
        
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        payload = {
            "model": self.config.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens or self.config.max_tokens,
                "temperature": temperature or self.config.temperature
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result.get("message", {}).get("content", "")
                    
        except Exception as e:
            self.logger.error(f"Ollama API call failed: {e}")
            raise


class OpenAIClient(LLMClient):
    """OpenAI client for cloud LLM inference."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.openai.com/v1"
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using OpenAI API."""
        self._validate_messages(messages)
        
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        payload = {
            "model": self.config.model,
            "messages": openai_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}")
            raise


class ClaudeClient(LLMClient):
    """Anthropic Claude client for cloud LLM inference."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.anthropic.com/v1"
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using Claude API."""
        self._validate_messages(messages)
        
        # Convert messages to Claude format
        claude_messages = []
        for msg in messages:
            claude_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        payload = {
            "model": self.config.model,
            "messages": claude_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature
        }
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Claude API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result.get("content", [{}])[0].get("text", "")
                    
        except Exception as e:
            self.logger.error(f"Claude API call failed: {e}")
            raise


class GeminiClient(LLMClient):
    """Google Gemini client for cloud LLM inference."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("Google API key is required")
        
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using Gemini API."""
        self._validate_messages(messages)
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            gemini_messages.append({
                "role": msg.role,
                "parts": [{"text": msg.content}]
            })
        
        payload = {
            "contents": gemini_messages,
            "generationConfig": {
                "maxOutputTokens": max_tokens or self.config.max_tokens,
                "temperature": temperature or self.config.temperature
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/models/{self.config.model}:generateContent?key={self.api_key}",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Gemini API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    
        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}")
            raise


class LLMFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_client(config: LLMConfig) -> LLMClient:
        """Create an LLM client based on configuration."""
        if config.provider == "ollama":
            return OllamaClient(config)
        elif config.provider == "openai":
            return OpenAIClient(config)
        elif config.provider == "claude":
            return ClaudeClient(config)
        elif config.provider == "gemini":
            return GeminiClient(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")


class LLMManager:
    """Manager for LLM clients with conversation history."""
    
    def __init__(self):
        self.clients: Dict[str, LLMClient] = {}
        self.conversation_history: Dict[str, List[LLMMessage]] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_client(self, name: str, config: LLMConfig) -> None:
        """Register an LLM client."""
        self.clients[name] = LLMFactory.create_client(config)
        self.logger.info(f"Registered LLM client: {name} ({config.provider}/{config.model})")
    
    def get_client(self, name: str) -> LLMClient:
        """Get a registered LLM client."""
        if name not in self.clients:
            raise ValueError(f"LLM client not found: {name}")
        return self.clients[name]
    
    async def generate_response(
        self,
        client_name: str,
        messages: List[LLMMessage],
        conversation_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        include_history: bool = True
    ) -> str:
        """Generate a response with optional conversation history."""
        client = self.get_client(client_name)
        
        # Prepare messages with history if requested
        if include_history and conversation_id:
            history = self.conversation_history.get(conversation_id, [])
            all_messages = history + messages
        else:
            all_messages = messages
        
        # Generate response
        response = await client.generate(all_messages, max_tokens, temperature)
        
        # Update conversation history
        if conversation_id:
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            # Add new messages to history
            self.conversation_history[conversation_id].extend(messages)
            
            # Add assistant response to history
            self.conversation_history[conversation_id].append(
                LLMMessage(role="assistant", content=response)
            )
            
            # Limit history length (keep last 20 messages)
            if len(self.conversation_history[conversation_id]) > 20:
                self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-20:]
        
        return response
    
    def clear_conversation_history(self, conversation_id: str) -> None:
        """Clear conversation history for a specific conversation."""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            self.logger.info(f"Cleared conversation history: {conversation_id}")


# Global LLM manager instance
llm_manager = LLMManager() 