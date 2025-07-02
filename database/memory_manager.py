"""
Memory management system for hierarchical agent memory.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import json
import hashlib

from .manager import get_db_session
from .models import Memory, MemoryRelationship, Agent

logger = logging.getLogger(__name__)


class MemoryType:
    """Memory type constants."""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryCategory:
    """Memory category constants."""
    CONVERSATION = "conversation"
    TASK = "task"
    KNOWLEDGE = "knowledge"
    PATTERN = "pattern"
    SOLUTION = "solution"
    CONTEXT = "context"


class MemoryManager:
    """Manages hierarchical memory operations for agents."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def store_memory(
        self,
        agent_name: str,
        memory_type: str,
        memory_category: str,
        content: str,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance: Optional[float] = None,
        confidence: float = 1.0,
        related_memory_ids: Optional[List[int]] = None
    ) -> Optional[int]:
        """Store a new memory for an agent."""
        try:
            with get_db_session() as session:
                # Get agent
                agent = session.query(Agent).filter(Agent.name == agent_name).first()
                if not agent:
                    self.logger.error(f"Agent not found: {agent_name}")
                    return None
                
                # Calculate importance if not provided
                if importance is None:
                    importance = self._calculate_importance(memory_type, memory_category, content)
                
                # Create memory
                memory = Memory(
                    agent_id=agent.id,
                    memory_type=memory_type,
                    memory_category=memory_category,
                    content=content,
                    context=context,
                    tags=tags or [],
                    importance=importance,
                    confidence=confidence,
                    related_memories=related_memory_ids or []
                )
                
                session.add(memory)
                session.commit()
                session.refresh(memory)
                
                # Create relationships if provided
                if related_memory_ids:
                    self._create_memory_relationships(session, memory.id, related_memory_ids)
                
                self.logger.info(f"Stored {memory_type} memory for {agent_name}: {memory.id}")
                return memory.id
                
        except Exception as e:
            self.logger.error(f"Failed to store memory for {agent_name}: {e}")
            return None
    
    def retrieve_memories(
        self,
        agent_name: str,
        memory_type: Optional[str] = None,
        memory_category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve memories for an agent with filtering."""
        try:
            with get_db_session() as session:
                # Get agent
                agent = session.query(Agent).filter(Agent.name == agent_name).first()
                if not agent:
                    self.logger.error(f"Agent not found: {agent_name}")
                    return []
                
                # Build query
                query = session.query(Memory).filter(Memory.agent_id == agent.id)
                
                if memory_type:
                    query = query.filter(Memory.memory_type == memory_type)
                
                if memory_category:
                    query = query.filter(Memory.memory_category == memory_category)
                
                if tags:
                    # Filter by tags (JSON array contains)
                    for tag in tags:
                        query = query.filter(Memory.tags.contains([tag]))
                
                query = query.filter(Memory.importance >= min_importance)
                
                # Order by importance and recency
                query = query.order_by(desc(Memory.importance), desc(Memory.accessed_at))
                
                # Limit results
                memories = query.limit(limit).all()
                
                # Update access count and timestamp
                for memory in memories:
                    memory.access_count += 1
                    memory.accessed_at = datetime.utcnow()
                
                session.commit()
                
                # Convert to dictionaries
                result = []
                for memory in memories:
                    memory_dict = {
                        "id": memory.id,
                        "memory_type": memory.memory_type,
                        "memory_category": memory.memory_category,
                        "content": memory.content,
                        "importance": memory.importance,
                        "confidence": memory.confidence,
                        "access_count": memory.access_count,
                        "created_at": memory.created_at.isoformat(),
                        "accessed_at": memory.accessed_at.isoformat(),
                        "tags": memory.tags,
                        "related_memories": memory.related_memories
                    }
                    
                    if include_context and memory.context:
                        memory_dict["context"] = memory.context
                    
                    result.append(memory_dict)
                
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve memories for {agent_name}: {e}")
            return []
    
    def search_memories(
        self,
        agent_name: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by content similarity (simple text search)."""
        try:
            with get_db_session() as session:
                # Get agent
                agent = session.query(Agent).filter(Agent.name == agent_name).first()
                if not agent:
                    self.logger.error(f"Agent not found: {agent_name}")
                    return []
                
                # Build query
                db_query = session.query(Memory).filter(Memory.agent_id == agent.id)
                
                if memory_type:
                    db_query = db_query.filter(Memory.memory_type == memory_type)
                
                # Simple text search (can be enhanced with vector search later)
                search_terms = query.lower().split()
                conditions = []
                for term in search_terms:
                    conditions.append(Memory.content.ilike(f"%{term}%"))
                    conditions.append(Memory.context.ilike(f"%{term}%"))
                
                if conditions:
                    db_query = db_query.filter(or_(*conditions))
                
                # Order by relevance (importance + recency)
                db_query = db_query.order_by(
                    desc(Memory.importance),
                    desc(Memory.accessed_at)
                )
                
                memories = db_query.limit(limit).all()
                
                # Update access counts
                for memory in memories:
                    memory.access_count += 1
                    memory.accessed_at = datetime.utcnow()
                
                session.commit()
                
                # Convert to dictionaries
                result = []
                for memory in memories:
                    result.append({
                        "id": memory.id,
                        "memory_type": memory.memory_type,
                        "memory_category": memory.memory_category,
                        "content": memory.content,
                        "importance": memory.importance,
                        "confidence": memory.confidence,
                        "created_at": memory.created_at.isoformat(),
                        "tags": memory.tags
                    })
                
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to search memories for {agent_name}: {e}")
            return []
    
    def consolidate_memories(self, agent_name: str, memory_type: str = MemoryType.EPISODIC) -> int:
        """Consolidate episodic memories into semantic memories."""
        try:
            with get_db_session() as session:
                # Get agent
                agent = session.query(Agent).filter(Agent.name == agent_name).first()
                if not agent:
                    self.logger.error(f"Agent not found: {agent_name}")
                    return 0
                
                # Get episodic memories that haven't been consolidated recently
                cutoff_date = datetime.utcnow() - timedelta(hours=24)
                episodic_memories = session.query(Memory).filter(
                    and_(
                        Memory.agent_id == agent.id,
                        Memory.memory_type == MemoryType.EPISODIC,
                        or_(
                            Memory.last_consolidated.is_(None),
                            Memory.last_consolidated < cutoff_date
                        )
                    )
                ).all()
                
                consolidated_count = 0
                
                for memory in episodic_memories:
                    # Check if this memory should be consolidated
                    if self._should_consolidate(memory):
                        # Create semantic memory from episodic memory
                        semantic_content = self._consolidate_content(memory.content, memory.context)
                        
                        semantic_memory = Memory(
                            agent_id=agent.id,
                            memory_type=MemoryType.SEMANTIC,
                            memory_category=memory.memory_category,
                            content=semantic_content,
                            context=f"Consolidated from episodic memory {memory.id}",
                            tags=memory.tags,
                            importance=min(memory.importance * 1.1, 1.0),  # Slight boost
                            confidence=memory.confidence,
                            related_memories=[memory.id]
                        )
                        
                        session.add(semantic_memory)
                        
                        # Mark episodic memory as consolidated
                        memory.last_consolidated = datetime.utcnow()
                        consolidated_count += 1
                
                session.commit()
                self.logger.info(f"Consolidated {consolidated_count} memories for {agent_name}")
                return consolidated_count
                
        except Exception as e:
            self.logger.error(f"Failed to consolidate memories for {agent_name}: {e}")
            return 0
    
    def decay_memories(self, agent_name: str, days_old: int = 30) -> int:
        """Decay old, low-importance memories."""
        try:
            with get_db_session() as session:
                # Get agent
                agent = session.query(Agent).filter(Agent.name == agent_name).first()
                if not agent:
                    self.logger.error(f"Agent not found: {agent_name}")
                    return 0
                
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)
                
                # Find memories to decay
                memories_to_decay = session.query(Memory).filter(
                    and_(
                        Memory.agent_id == agent.id,
                        Memory.created_at < cutoff_date,
                        Memory.importance < 0.3,  # Low importance
                        Memory.access_count < 5   # Rarely accessed
                    )
                ).all()
                
                decayed_count = 0
                for memory in memories_to_decay:
                    # Reduce importance
                    memory.importance *= 0.8
                    
                    # If importance is very low, mark for deletion
                    if memory.importance < 0.1:
                        session.delete(memory)
                        decayed_count += 1
                
                session.commit()
                self.logger.info(f"Decayed {decayed_count} memories for {agent_name}")
                return decayed_count
                
        except Exception as e:
            self.logger.error(f"Failed to decay memories for {agent_name}: {e}")
            return 0
    
    def get_memory_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get memory statistics for an agent."""
        try:
            with get_db_session() as session:
                # Get agent
                agent = session.query(Agent).filter(Agent.name == agent_name).first()
                if not agent:
                    self.logger.error(f"Agent not found: {agent_name}")
                    return {}
                
                # Get counts by type
                working_count = session.query(Memory).filter(
                    and_(Memory.agent_id == agent.id, Memory.memory_type == MemoryType.WORKING)
                ).count()
                
                episodic_count = session.query(Memory).filter(
                    and_(Memory.agent_id == agent.id, Memory.memory_type == MemoryType.EPISODIC)
                ).count()
                
                semantic_count = session.query(Memory).filter(
                    and_(Memory.agent_id == agent.id, Memory.memory_type == MemoryType.SEMANTIC)
                ).count()
                
                # Get average importance
                avg_importance = session.query(func.avg(Memory.importance)).filter(
                    Memory.agent_id == agent.id
                ).scalar() or 0.0
                
                return {
                    "agent_name": agent_name,
                    "working_memories": working_count,
                    "episodic_memories": episodic_count,
                    "semantic_memories": semantic_count,
                    "total_memories": working_count + episodic_count + semantic_count,
                    "average_importance": round(avg_importance, 3)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get memory stats for {agent_name}: {e}")
            return {}
    
    def _calculate_importance(self, memory_type: str, memory_category: str, content: str) -> float:
        """Calculate memory importance based on type, category, and content."""
        base_importance = 0.5
        
        # Adjust by memory type
        if memory_type == MemoryType.WORKING:
            base_importance *= 0.7  # Working memory is less important
        elif memory_type == MemoryType.SEMANTIC:
            base_importance *= 1.2  # Semantic memory is more important
        
        # Adjust by category
        if memory_category == MemoryCategory.SOLUTION:
            base_importance *= 1.3  # Solutions are important
        elif memory_category == MemoryCategory.PATTERN:
            base_importance *= 1.2  # Patterns are important
        elif memory_category == MemoryCategory.KNOWLEDGE:
            base_importance *= 1.1  # Knowledge is important
        
        # Adjust by content length (longer content might be more important)
        content_length_factor = min(len(content) / 100, 2.0)  # Cap at 2x
        base_importance *= content_length_factor
        
        return min(base_importance, 1.0)  # Cap at 1.0
    
    def _should_consolidate(self, memory: Memory) -> bool:
        """Determine if a memory should be consolidated."""
        # Consolidate if memory is important and has been accessed multiple times
        return memory.importance > 0.6 and memory.access_count > 3
    
    def _consolidate_content(self, content: str, context: Optional[str]) -> str:
        """Consolidate episodic content into semantic content."""
        # Simple consolidation - can be enhanced with AI summarization
        if context:
            return f"Learned: {content} (Context: {context})"
        else:
            return f"Learned: {content}"
    
    def _create_memory_relationships(
        self,
        session: Session,
        memory_id: int,
        related_memory_ids: List[int]
    ) -> None:
        """Create relationships between memories."""
        for related_id in related_memory_ids:
            relationship = MemoryRelationship(
                source_memory_id=memory_id,
                target_memory_id=related_id,
                relationship_type="related",
                strength=1.0
            )
            session.add(relationship)


# Global memory manager instance
memory_manager = MemoryManager() 