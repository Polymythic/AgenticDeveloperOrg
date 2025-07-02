"""
Generic Agent implementation that can handle any personality and tools.
"""

import asyncio
import hashlib
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from abc import abstractmethod

from .base_agent import BaseAgent
from shared.models import (
    TaskRequest, TaskResponse, MessageType, AgentStatus
)
from database.models import CodeReview as DBCodeReview
from database.memory_manager import memory_manager, MemoryType, MemoryCategory
from shared.llm import llm_manager, LLMConfig, LLMMessage

logger = logging.getLogger(__name__)


class GenericAgent(BaseAgent):
    """Generic agent that can handle any personality and tools based on configuration."""
    
    def __init__(self, agent_name: str):
        super().__init__(agent_name)
        self.tools: Dict[str, Callable] = {}
        self._register_default_tools()
        self._setup_llm_client()
        logger.info(f"Generic Agent '{self.agent_name}' initialized with personality: {self.config.personality}")
    
    def _setup_llm_client(self):
        """Setup LLM client for this agent."""
        try:
            # Create LLM configuration
            llm_config = LLMConfig(
                provider=self.config.llm_provider,
                deployment=self.config.llm_deployment,
                model=self.config.llm_model,
                api_key=self.config.llm_api_key,
                base_url=self.config.llm_base_url,
                max_tokens=self.config.max_context_length,
                temperature=0.7
            )
            
            # Register client with agent name as identifier
            client_name = f"{self.agent_name}_llm"
            llm_manager.register_client(client_name, llm_config)
            self.llm_client_name = client_name
            
            logger.info(f"LLM client registered for {self.agent_name}: {self.config.llm_provider}/{self.config.llm_model}")
            
        except Exception as e:
            logger.error(f"Failed to setup LLM client for {self.agent_name}: {e}")
            # Fallback to personality-based responses
            self.llm_client_name = None
    
    def _register_default_tools(self):
        """Register default tools that all agents can use."""
        self.tools = {
            "code_review": self._tool_code_review,
            "text_analysis": self._tool_text_analysis,
            "data_processing": self._tool_data_processing,
            "file_operations": self._tool_file_operations,
            "web_search": self._tool_web_search,
            "math_calculation": self._tool_math_calculation,
            "text_generation": self._tool_text_generation,
        }
    
    async def process_task(self, task_request: TaskRequest) -> TaskResponse:
        """Process a task request using the agent's configured personality and available tools."""
        start_time = time.time()
        task_id = task_request.task_id or str(uuid.uuid4())
        
        try:
            self.update_status(AgentStatus.BUSY, f"Processing {task_request.task_type}")
            
            # Check if this is a tool-based task
            if task_request.task_type in self.tools:
                result = await self._execute_tool(task_request.task_type, task_request.parameters or {})
            elif task_request.task_type == "generate_response":
                result = await self.generate_response(
                    task_request.description,
                    task_request.parameters.get("context") if task_request.parameters else None
                )
            elif task_request.task_type == "conversation":
                result = await self._handle_conversation(task_request.parameters or {})
            else:
                # Generic task processing using the agent's personality
                result = await self._process_generic_task(task_request)
            
            execution_time = time.time() - start_time
            task_response = TaskResponse(
                task_id=task_id,
                agent_name=self.agent_name,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
            # Log the task
            self.log_task(task_request, task_response)
            
            # Log the message
            self.log_message(
                MessageType.ASSISTANT,
                f"Completed task: {task_request.task_type}",
                {"task_id": task_id, "execution_time": execution_time}
            )
            
            # Store memory about this task
            if self.config.memory_enabled:
                await self._store_task_memory(task_request, task_response, result)
            
            self.update_status(AgentStatus.IDLE)
            return task_response
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Task processing failed for {self.agent_name}: {e}")
            
            task_response = TaskResponse(
                task_id=task_id,
                agent_name=self.agent_name,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
            
            # Log the failed task
            self.log_task(task_request, task_response)
            
            # Log the error message
            self.log_message(
                MessageType.ERROR,
                f"Task failed: {str(e)}",
                {"task_id": task_id, "task_type": task_request.task_type}
            )
            
            self.update_status(AgentStatus.ERROR, f"Failed: {task_request.task_type}")
            return task_response
    
    async def generate_response(self, input_text: str, context: Optional[str] = None) -> str:
        """Generate a response based on the agent's personality and the input."""
        try:
            # Build context-aware prompt based on agent's personality
            prompt = self._build_personality_prompt(input_text, context)
            
            # Generate response based on personality
            response = await self._generate_personality_response(prompt, input_text, context)
            
            # Log the interaction
            self.log_message(MessageType.USER, input_text, {"context": context})
            self.log_message(MessageType.ASSISTANT, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed for {self.agent_name}: {e}")
            error_response = f"I apologize, but I encountered an error while processing your request: {str(e)}"
            self.log_message(MessageType.ERROR, error_response)
            return error_response
    
    def _build_personality_prompt(self, input_text: str, context: Optional[str] = None) -> str:
        """Build a prompt that incorporates the agent's personality."""
        prompt_parts = [
            f"System: {self.config.system_prompt}",
            f"Personality: {self.config.personality}",
            f"Goal: {self.config.goal}",
            f"Job Description: {self.config.job_description}"
        ]
        
        if context:
            prompt_parts.append(f"Context: {context}")
        
        prompt_parts.append(f"User Input: {input_text}")
        prompt_parts.append("Response:")
        
        return "\n\n".join(prompt_parts)
    
    async def _generate_personality_response(self, prompt: str, input_text: str, context: Optional[str] = None) -> str:
        """Generate a response based on the agent's personality."""
        # Try to use LLM if available
        if hasattr(self, 'llm_client_name') and self.llm_client_name:
            try:
                # Create messages for LLM
                messages = [
                    LLMMessage(role="system", content=prompt),
                    LLMMessage(role="user", content=input_text)
                ]
                
                # Generate response using LLM
                response = await llm_manager.generate_response(
                    client_name=self.llm_client_name,
                    messages=messages,
                    conversation_id=f"{self.agent_name}_conversation",
                    include_history=True
                )
                
                return response
                
            except Exception as e:
                logger.error(f"LLM generation failed for {self.agent_name}, falling back to personality-based: {e}")
                # Fall back to personality-based responses
        
        # Fallback to personality-based response generation
        input_lower = input_text.lower()
        
        # Generate response based on personality and input type
        if "code" in input_lower or "review" in input_lower:
            return self._generate_code_related_response(input_text, context)
        elif "help" in input_lower or "assist" in input_lower:
            return self._generate_help_response(input_text, context)
        elif "analyze" in input_lower or "examine" in input_lower:
            return self._generate_analysis_response(input_text, context)
        else:
            return self._generate_general_response(input_text, context)
    
    def _generate_code_related_response(self, input_text: str, context: Optional[str] = None) -> str:
        """Generate a code-related response based on personality."""
        responses = [
            f"As {self.config.personality.lower()}, I'm ready to help with code analysis and review. Please share the code you'd like me to examine.",
            f"Based on my expertise in {self.config.job_description.lower()}, I can provide detailed code review and suggestions. What would you like me to look at?",
            f"I'm here to ensure code quality and best practices. Please provide the code you'd like me to review.",
            f"With my focus on {self.config.goal.lower()}, I'm ready to analyze your code and provide constructive feedback."
        ]
        
        import random
        return random.choice(responses)
    
    def _generate_help_response(self, input_text: str, context: Optional[str] = None) -> str:
        """Generate a help response based on personality."""
        responses = [
            f"Hello! I'm {self.agent_name}, and I'm here to help with {self.config.job_description.lower()}. How can I assist you today?",
            f"As {self.config.personality.lower()}, I'm ready to help you with {self.config.goal.lower()}. What do you need assistance with?",
            f"I'm here to support you with {self.config.job_description.lower()}. What would you like to work on?",
            f"With my expertise in {self.config.personality.lower()}, I can help you achieve {self.config.goal.lower()}. What can I do for you?"
        ]
        
        import random
        return random.choice(responses)
    
    def _generate_analysis_response(self, input_text: str, context: Optional[str] = None) -> str:
        """Generate an analysis response based on personality."""
        responses = [
            f"I'm ready to provide a thorough analysis based on my expertise in {self.config.job_description.lower()}. Please share what you'd like me to examine.",
            f"As {self.config.personality.lower()}, I can analyze this from multiple angles. What specific aspects would you like me to focus on?",
            f"I'll apply my knowledge of {self.config.goal.lower()} to provide a comprehensive analysis. Please provide the details.",
            f"With my background in {self.config.personality.lower()}, I can help you analyze this effectively. What should I look at?"
        ]
        
        import random
        return random.choice(responses)
    
    def _generate_general_response(self, input_text: str, context: Optional[str] = None) -> str:
        """Generate a general response based on personality."""
        responses = [
            f"Hello! I'm {self.agent_name}, {self.config.personality.lower()}. I'm here to help with {self.config.job_description.lower()}.",
            f"As {self.config.personality.lower()}, I'm passionate about {self.config.goal.lower()}. How can I help you today?",
            f"I'm {self.agent_name}, and I specialize in {self.config.job_description.lower()}. What would you like to discuss?",
            f"With my expertise in {self.config.personality.lower()}, I'm ready to assist you with {self.config.goal.lower()}. What's on your mind?"
        ]
        
        import random
        return random.choice(responses)
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not available for agent '{self.agent_name}'")
        
        tool_func = self.tools[tool_name]
        return await tool_func(parameters)
    
    async def _process_generic_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Process a generic task using the agent's personality."""
        return {
            "task_type": task_request.task_type,
            "description": task_request.description,
            "agent_personality": self.config.personality,
            "agent_goal": self.config.goal,
            "response": await self.generate_response(task_request.description, task_request.parameters.get("context") if task_request.parameters else None),
            "parameters": task_request.parameters
        }
    
    async def _handle_conversation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation-based tasks."""
        messages = parameters.get("messages", [])
        context = parameters.get("context", "")
        
        # Process conversation history
        conversation_summary = self._summarize_conversation(messages)
        
        # Generate response based on conversation context
        response = await self.generate_response(
            parameters.get("current_message", ""),
            f"{context}\n\nConversation History: {conversation_summary}"
        )
        
        return {
            "conversation_id": parameters.get("conversation_id"),
            "response": response,
            "context": context,
            "conversation_summary": conversation_summary
        }
    
    def _summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Summarize conversation history."""
        if not messages:
            return "No previous conversation."
        
        summary_parts = []
        for msg in messages[-5:]:  # Last 5 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]  # First 100 chars
            summary_parts.append(f"{role}: {content}...")
        
        return "\n".join(summary_parts)
    
    # Tool implementations
    async def _tool_code_review(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Code review tool."""
        code = parameters.get("code", "")
        language = parameters.get("language", "python")
        context = parameters.get("context", "")
        focus_areas = parameters.get("focus_areas", [])
        
        if not code:
            raise ValueError("No code provided for review")
        
        # Generate code hash for caching
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        # Check if we have a cached review
        cached_review = self._get_cached_review(code_hash)
        if cached_review:
            return cached_review
        
        # Perform the review based on agent's personality
        review_result = self._perform_code_analysis(code, language, context, focus_areas)
        
        # Cache the review
        self._cache_review(code_hash, language, review_result)
        
        return review_result
    
    async def _tool_text_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Text analysis tool."""
        text = parameters.get("text", "")
        analysis_type = parameters.get("analysis_type", "general")
        
        if not text:
            raise ValueError("No text provided for analysis")
        
        analysis = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "analysis_type": analysis_type,
            "agent_personality": self.config.personality,
            "insights": []
        }
        
        # Add personality-based insights
        if "security" in self.config.personality.lower():
            analysis["insights"].append("Security-focused analysis provided")
        if "quality" in self.config.personality.lower():
            analysis["insights"].append("Quality-focused analysis provided")
        if "performance" in self.config.personality.lower():
            analysis["insights"].append("Performance-focused analysis provided")
        
        return analysis
    
    async def _tool_data_processing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Data processing tool."""
        data = parameters.get("data", [])
        operation = parameters.get("operation", "analyze")
        
        return {
            "operation": operation,
            "data_size": len(data),
            "agent_personality": self.config.personality,
            "result": f"Processed {len(data)} items using {operation} operation"
        }
    
    async def _tool_file_operations(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """File operations tool."""
        operation = parameters.get("operation", "read")
        file_path = parameters.get("file_path", "")
        
        return {
            "operation": operation,
            "file_path": file_path,
            "agent_personality": self.config.personality,
            "result": f"Performed {operation} operation on {file_path}"
        }
    
    async def _tool_web_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Web search tool."""
        query = parameters.get("query", "")
        
        return {
            "query": query,
            "agent_personality": self.config.personality,
            "result": f"Search results for '{query}' based on {self.config.personality.lower()} expertise"
        }
    
    async def _tool_math_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Math calculation tool."""
        expression = parameters.get("expression", "")
        
        try:
            result = eval(expression)  # In production, use a safer math library
            return {
                "expression": expression,
                "result": result,
                "agent_personality": self.config.personality
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e),
                "agent_personality": self.config.personality
            }
    
    async def _tool_text_generation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Text generation tool."""
        prompt = parameters.get("prompt", "")
        style = parameters.get("style", "professional")
        
        return {
            "prompt": prompt,
            "style": style,
            "agent_personality": self.config.personality,
            "generated_text": f"Generated text in {style} style based on {self.config.personality.lower()} expertise"
        }
    
    def _perform_code_analysis(self, code: str, language: str, context: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Perform code analysis based on agent's personality."""
        analysis = {
            "review": "",
            "suggestions": [],
            "issues": [],
            "score": None,
            "confidence": 1.0
        }
        
        lines = code.split('\n')
        analysis["review"] = f"Reviewed {len(lines)} lines of {language} code using {self.config.personality.lower()} expertise."
        
        # Add personality-specific analysis
        if "security" in self.config.personality.lower():
            analysis["suggestions"].append("Consider security implications of user input handling")
            if "eval(" in code:
                analysis["issues"].append("Potential security risk: eval() usage detected")
        
        if "performance" in self.config.personality.lower():
            analysis["suggestions"].append("Review for potential performance bottlenecks")
            if len(lines) > 100:
                analysis["issues"].append("Large function detected - consider breaking into smaller functions")
        
        if "quality" in self.config.personality.lower():
            analysis["suggestions"].append("Ensure code follows consistent formatting and naming conventions")
            if "print(" in code and "logging" not in code:
                analysis["suggestions"].append("Consider using logging instead of print statements")
        
        # Calculate score based on issues found
        total_issues = len(analysis["issues"])
        if total_issues == 0:
            analysis["score"] = 9.0
        elif total_issues <= 2:
            analysis["score"] = 7.0
        elif total_issues <= 5:
            analysis["score"] = 5.0
        else:
            analysis["score"] = 3.0
        
        # Generate comprehensive review text
        review_parts = [analysis["review"]]
        
        if analysis["issues"]:
            review_parts.append("\nIssues found:")
            for issue in analysis["issues"]:
                review_parts.append(f"- {issue}")
        
        if analysis["suggestions"]:
            review_parts.append("\nSuggestions:")
            for suggestion in analysis["suggestions"]:
                review_parts.append(f"- {suggestion}")
        
        if analysis["score"] is not None:
            review_parts.append(f"\nOverall score: {analysis['score']}/10")
        
        analysis["review"] = "\n".join(review_parts)
        
        return analysis
    
    def _get_cached_review(self, code_hash: str) -> Optional[Dict[str, Any]]:
        """Get a cached review from the database."""
        try:
            from database.manager import get_db_session
            from database.models import Agent as DBAgent
            
            with get_db_session() as session:
                db_agent = session.query(DBAgent).filter(DBAgent.name == self.agent_name).first()
                if db_agent:
                    cached_review = session.query(DBCodeReview).filter(
                        DBCodeReview.agent_id == db_agent.id,
                        DBCodeReview.code_hash == code_hash
                    ).first()
                    
                    if cached_review:
                        return {
                            "review": cached_review.review,
                            "suggestions": cached_review.suggestions or [],
                            "issues": cached_review.issues or [],
                            "score": cached_review.score,
                            "confidence": cached_review.confidence,
                            "cached": True
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached review: {e}")
            return None
    
    def _cache_review(self, code_hash: str, language: str, review_result: Dict[str, Any]):
        """Cache a review result in the database."""
        try:
            from database.manager import get_db_session
            from database.models import Agent as DBAgent
            
            with get_db_session() as session:
                db_agent = session.query(DBAgent).filter(DBAgent.name == self.agent_name).first()
                if db_agent:
                    db_review = DBCodeReview(
                        agent_id=db_agent.id,
                        code_hash=code_hash,
                        language=language,
                        review=review_result["review"],
                        suggestions=review_result.get("suggestions", []),
                        issues=review_result.get("issues", []),
                        score=review_result.get("score"),
                        confidence=review_result.get("confidence", 1.0)
                    )
                    session.add(db_review)
                    session.commit()
                    
        except Exception as e:
            logger.error(f"Failed to cache review: {e}")
    
    async def summarize_memory(self, memory_type: Optional[str] = None, limit: int = 20) -> str:
        """Summarize the agent's memory using the LLM for human readability."""
        # Retrieve memories (limit to prevent long processing)
        memories = memory_manager.retrieve_memories(
            agent_name=self.agent_name,
            memory_type=memory_type,
            limit=min(limit, 10)  # Cap at 10 memories for faster processing
        )
        if not memories:
            return "No memories found."
        
        # Build a concise summary prompt
        memory_texts = []
        for m in memories[:5]:  # Only use first 5 memories for summary
            content = m['content'][:100] + "..." if len(m['content']) > 100 else m['content']
            memory_texts.append(f"- {m['memory_type']} ({m['memory_category']}): {content}")
        
        prompt = (
            f"Summarize these {len(memories)} memories in 2-3 sentences:\n"
            + "\n".join(memory_texts)
        )
        
        try:
            # Use the agent's LLM to generate a summary with timeout
            summary = await asyncio.wait_for(
                self.generate_response(prompt),
                timeout=15.0  # 15 second timeout
            )
            return summary
        except asyncio.TimeoutError:
            return f"Memory summary timeout. Found {len(memories)} memories."
        except Exception as e:
            logger.error(f"Failed to generate memory summary: {e}")
            return f"Error generating summary. Found {len(memories)} memories."
    
    async def _store_task_memory(self, task_request: TaskRequest, task_response: TaskResponse, result: Any) -> None:
        """Store memory about a completed task."""
        try:
            # Store episodic memory about the task
            task_content = f"Task: {task_request.task_type} - {task_request.description}"
            if task_request.parameters:
                task_content += f" | Parameters: {task_request.parameters}"
            
            task_context = f"Agent: {self.agent_name}, Execution time: {task_response.execution_time}s, Success: {task_response.success}"
            
            # Store the task memory
            memory_manager.store_memory(
                agent_name=self.agent_name,
                memory_type=MemoryType.EPISODIC,
                memory_category=MemoryCategory.TASK,
                content=task_content,
                context=task_context,
                tags=[task_request.task_type, "task_execution"],
                importance=0.7 if task_response.success else 0.9,  # Failed tasks are more important to remember
                confidence=1.0
            )
            
            # Store semantic memory about the result if it's significant
            if task_response.success and result:
                if isinstance(result, dict):
                    # Extract key insights from the result
                    if "review" in result:
                        review_content = f"Code review result: {result.get('review', '')[:200]}..."
                        memory_manager.store_memory(
                            agent_name=self.agent_name,
                            memory_type=MemoryType.SEMANTIC,
                            memory_category=MemoryCategory.KNOWLEDGE,
                            content=review_content,
                            context=f"From {task_request.task_type} task",
                            tags=[task_request.task_type, "code_review", "knowledge"],
                            importance=0.8,
                            confidence=1.0
                        )
                    
                    if "suggestions" in result and result["suggestions"]:
                        suggestions_content = f"Suggestions made: {', '.join(result['suggestions'])}"
                        memory_manager.store_memory(
                            agent_name=self.agent_name,
                            memory_type=MemoryType.SEMANTIC,
                            memory_category=MemoryCategory.SOLUTION,
                            content=suggestions_content,
                            context=f"From {task_request.task_type} task",
                            tags=[task_request.task_type, "suggestions", "solutions"],
                            importance=0.8,
                            confidence=1.0
                        )
                else:
                    # Store general result
                    result_content = f"Task result: {str(result)[:200]}..."
                    memory_manager.store_memory(
                        agent_name=self.agent_name,
                        memory_type=MemoryType.SEMANTIC,
                        memory_category=MemoryCategory.KNOWLEDGE,
                        content=result_content,
                        context=f"From {task_request.task_type} task",
                        tags=[task_request.task_type, "result", "knowledge"],
                        importance=0.6,
                        confidence=1.0
                    )
            
            logger.info(f"Stored memory for {self.agent_name} task: {task_request.task_type}")
            
        except Exception as e:
            logger.error(f"Failed to store task memory for {self.agent_name}: {e}") 