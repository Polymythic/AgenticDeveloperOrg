"""
Main FastAPI application for the multi-agent system.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.models import (
    TaskRequest, TaskResponse, CodeReviewRequest, CodeReviewResponse,
    HealthCheck, AgentState
)
from shared.config import get_config
from database.manager import init_database, get_db_manager
from agents.manager import initialize_agents, shutdown_agents, get_agent_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Multi-Agent Software Development System...")
    
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized")
        
        # Initialize agents
        await initialize_agents()
        logger.info("Agents initialized")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-Agent Software Development System...")
    
    try:
        await shutdown_agents()
        logger.info("Agents shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Software Development System",
    description="A Docker-based multi-agent system for collaborative software development",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Multi-Agent Software Development System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    try:
        config = get_config()
        db_manager = get_db_manager()
        
        # Check database health
        db_health = db_manager.health_check()
        
        # Check agents health
        agent_manager = await get_agent_manager()
        agent_states = await agent_manager.get_agent_states()
        
        # Convert agent states to the expected format
        agents = []
        for state in agent_states:
            agents.append(AgentState(
                name=state["name"],
                status=state["status"],
                current_task=state["current_task"],
                memory_usage=state["memory_usage"],
                last_activity=state["last_activity"],
                agent_metadata=state["agent_metadata"]
            ))
        
        return HealthCheck(
            status="healthy" if db_health["status"] == "healthy" else "unhealthy",
            version=config.app.version,
            agents=agents,
            database_status=db_health["status"],
            integrations={
                "slack": "disabled",
                "github": "disabled"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            version="1.0.0",
            agents=[],
            database_status="error",
            integrations={
                "slack": "error",
                "github": "error"
            }
        )


@app.get("/agents", response_model=List[Dict[str, Any]])
async def list_agents():
    """List all agents."""
    try:
        agent_manager = await get_agent_manager()
        return await agent_manager.get_agent_states()
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}", response_model=Dict[str, Any])
async def get_agent(agent_name: str):
    """Get information about a specific agent."""
    try:
        agent_manager = await get_agent_manager()
        agent = await agent_manager.get_agent(agent_name)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")
        
        return agent.get_state()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/tasks", response_model=TaskResponse)
async def submit_task(agent_name: str, task_request: TaskRequest):
    """Submit a task to a specific agent."""
    try:
        # Override the agent name in the request
        task_request.agent_name = agent_name
        
        agent_manager = await get_agent_manager()
        return await agent_manager.submit_task(task_request)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit task to {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks", response_model=TaskResponse)
async def submit_task_to_any_agent(task_request: TaskRequest):
    """Submit a task to any available agent."""
    try:
        agent_manager = await get_agent_manager()
        return await agent_manager.submit_task_to_any_agent(
            task_request.task_type,
            task_request.description,
            **(task_request.parameters or {})
        )
        
    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/code-review", response_model=CodeReviewResponse)
async def review_code(code_request: CodeReviewRequest):
    """Review code using the code reviewer agent."""
    try:
        agent_manager = await get_agent_manager()
        
        # Submit code review task
        task_response = await agent_manager.submit_task_to_any_agent(
            "code_review",
            f"Review {code_request.language} code",
            code=code_request.code,
            language=code_request.language,
            context=code_request.context,
            focus_areas=code_request.focus_areas or []
        )
        
        if not task_response.success:
            raise HTTPException(status_code=500, detail=task_response.error_message)
        
        # Convert task response to code review response
        result = task_response.result
        return CodeReviewResponse(
            review=result["review"],
            suggestions=result.get("suggestions", []),
            issues=result.get("issues", []),
            score=result.get("score"),
            confidence=result.get("confidence", 1.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/restart")
async def restart_agent(agent_name: str):
    """Restart a specific agent."""
    try:
        agent_manager = await get_agent_manager()
        success = await agent_manager.restart_agent(agent_name)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to restart agent: {agent_name}")
        
        return {"message": f"Agent {agent_name} restarted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/database/health")
async def database_health():
    """Get database health information."""
    try:
        db_manager = get_db_manager()
        return db_manager.health_check()
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/database/backup")
async def backup_database():
    """Create a database backup."""
    try:
        db_manager = get_db_manager()
        success = db_manager.backup_database()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create database backup")
        
        return {"message": "Database backup created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/database/cleanup")
async def cleanup_database(days: int = 30):
    """Clean up old data from the database."""
    try:
        db_manager = get_db_manager()
        deleted_count = db_manager.cleanup_old_data(days)
        
        return {
            "message": f"Database cleanup completed",
            "deleted_records": deleted_count,
            "days_old": days
        }
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_configuration():
    """Get the current configuration."""
    try:
        config = get_config()
        return {
            "app": config.app.dict(),
            "api": config.api.dict(),
            "database": config.database.dict(),
            "logging": config.logging.dict(),
            "agents": [agent.dict() for agent in config.agents],
            "integrations": config.integrations.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    uvicorn.run(
        "main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.app.debug,
        log_level=config.logging.level.lower()
    ) 