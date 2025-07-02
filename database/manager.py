"""
Database manager for the multi-agent system.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from .models import Base
from shared.config import get_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for handling database operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.config = get_config()
        self.database_url = database_url or f"sqlite:///{self.config.database.path}"
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database engine and session factory."""
        try:
            # Ensure database directory exists
            db_path = Path(self.config.database.path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create engine
            self.engine = create_engine(
                self.database_url,
                echo=self.config.app.debug,
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info(f"Database setup complete: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database query failed: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            with self.get_session() as session:
                # Test basic query
                result = session.execute(text("SELECT 1 as test"))
                result.fetchone()
                
                # Get table counts
                tables = ["agents", "agent_states", "conversations", "messages", "tasks", "memories", "code_reviews"]
                table_counts = {}
                
                for table in tables:
                    try:
                        result = session.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                        count = result.fetchone()[0]
                        table_counts[table] = count
                    except Exception:
                        table_counts[table] = 0
                
                return {
                    "status": "healthy",
                    "database_url": self.database_url,
                    "table_counts": table_counts
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_url": self.database_url
            }
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """Create a backup of the database."""
        try:
            if not backup_path:
                backup_path = f"{self.config.database.path}.backup"
            
            # For SQLite, we can simply copy the file
            if "sqlite" in self.database_url:
                import shutil
                shutil.copy2(self.config.database.path, backup_path)
                logger.info(f"Database backup created: {backup_path}")
                return True
            else:
                # For other databases, implement specific backup logic
                logger.warning("Backup not implemented for non-SQLite databases")
                return False
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up old data from the database."""
        try:
            with self.get_session() as session:
                # Clean up old messages
                result = session.execute(
                    text("DELETE FROM messages WHERE timestamp < datetime('now', '-{} days')".format(days))
                )
                messages_deleted = result.rowcount
                
                # Clean up old tasks
                result = session.execute(
                    text("DELETE FROM tasks WHERE created_at < datetime('now', '-{} days')".format(days))
                )
                tasks_deleted = result.rowcount
                
                # Clean up old memories
                result = session.execute(
                    text("DELETE FROM memories WHERE created_at < datetime('now', '-{} days')".format(days))
                )
                memories_deleted = result.rowcount
                
                session.commit()
                
                total_deleted = messages_deleted + tasks_deleted + memories_deleted
                logger.info(f"Cleaned up {total_deleted} old records")
                return total_deleted
                
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return 0


# Global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get the global database manager."""
    return db_manager


def get_db_session() -> Session:
    """Get a database session."""
    return db_manager.get_session()


def init_database():
    """Initialize the database with tables."""
    db_manager.create_tables() 