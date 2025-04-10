"""
Logger Router for Markdown Forge.
Handles receiving and processing logs from the frontend.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..database import get_db
from ..utils.logger import setup_logging, log_to_file

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    responses={404: {"description": "Not found"}},
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/client")
async def log_from_client(
    log_data: Dict,
    background_tasks: BackgroundTasks,
):
    """
    Receive logs from the frontend client.
    
    The log data should contain:
    - level: str (debug, info, warning, error, critical)
    - message: str
    - timestamp: str (ISO format, optional)
    - source: str (component that generated the log)
    - details: Dict (additional context, optional)
    """
    try:
        # Validate log data
        level = log_data.get("level", "info").lower()
        message = log_data.get("message", "")
        timestamp = log_data.get("timestamp", datetime.now().isoformat())
        source = log_data.get("source", "frontend")
        details = log_data.get("details", {})
        
        # Map level string to logging level
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        
        log_level = level_map.get(level, logging.INFO)
        
        # Format the log message
        formatted_message = f"[{source}] {message}"
        if details:
            formatted_message += f" | Details: {details}"
            
        # Log using Python's logging
        logger.log(log_level, formatted_message)
        
        # Add background task to write to log file
        background_tasks.add_task(
            log_to_file,
            level=level,
            message=message,
            source=source,
            details=details,
            timestamp=timestamp
        )
        
        return {"status": "success", "message": "Log received"}
    
    except Exception as e:
        logger.error(f"Error processing client log: {str(e)}")
        return {"status": "error", "message": f"Error processing log: {str(e)}"}

@router.get("/recent")
async def get_recent_logs(
    limit: int = 100,
    level: Optional[str] = None,
    source: Optional[str] = None,
):
    """
    Get recent logs, with optional filtering by level and source.
    
    Args:
        limit: Maximum number of logs to return
        level: Filter by log level (debug, info, warning, error, critical)
        source: Filter by log source
        
    Returns:
        List of log entries
    """
    try:
        # In a real implementation, this would query logs from storage
        # For now, we'll return a placeholder response
        return {
            "status": "success",
            "message": "This endpoint will return recent logs from storage",
            "logs": []
        }
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}") 