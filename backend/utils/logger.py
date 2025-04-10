import logging
import os
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger instance for the given name.
    
    Args:
        name: Name of the logger (typically __name__)
        level: Optional logging level to override the default level
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Don't duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level from environment or default to INFO
    env_level = os.getenv("LOG_LEVEL", "INFO").upper()
    default_level = getattr(logging, env_level, logging.INFO)
    
    # Override with provided level if specified
    log_level = level if level is not None else default_level
    logger.setLevel(log_level)
    
    # Create log directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file with date
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"app_{today}.log")
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Create console handler with the same level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatters
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )
    
    # Add formatters to handlers
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class AsyncLogger:
    """
    Asynchronous logger wrapper for logging in async contexts.
    """
    
    def __init__(self, name: str, level: Optional[int] = None):
        """
        Initialize the async logger.
        
        Args:
            name: Name of the logger
            level: Optional logging level
        """
        self.logger = get_logger(name, level)
    
    async def debug(self, message: str, *args, **kwargs):
        """Log debug message asynchronously"""
        self.logger.debug(message, *args, **kwargs)
    
    async def info(self, message: str, *args, **kwargs):
        """Log info message asynchronously"""
        self.logger.info(message, *args, **kwargs)
    
    async def warning(self, message: str, *args, **kwargs):
        """Log warning message asynchronously"""
        self.logger.warning(message, *args, **kwargs)
    
    async def error(self, message: str, *args, **kwargs):
        """Log error message asynchronously"""
        self.logger.error(message, *args, **kwargs)
    
    async def critical(self, message: str, *args, **kwargs):
        """Log critical message asynchronously"""
        self.logger.critical(message, *args, **kwargs)

def get_async_logger(name: str, level: Optional[int] = None) -> AsyncLogger:
    """
    Get an asynchronous logger instance.
    
    Args:
        name: Name of the logger
        level: Optional logging level
        
    Returns:
        AsyncLogger instance
    """
    return AsyncLogger(name, level)

def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None
) -> None:
    """
    Set up logging configuration for the entire application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional custom log file path
    """
    # Create logs directory
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure client logs directory
    client_log_dir = os.path.join(log_dir, "client")
    os.makedirs(client_log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Clean existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set level
    level_value = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(level_value)
    
    # Default log file
    if log_file is None:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"app_{today}.log")
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level_value)
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level_value)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Log setup completion
    logging.info(f"Logging initialized at level {level}")
    logging.info(f"Log file: {log_file}")

async def log_to_file(
    level: str,
    message: str,
    source: str,
    details: Dict = None,
    timestamp: str = None
) -> None:
    """
    Log client-side messages to dedicated log files.
    
    Args:
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        source: Source of the log (component that generated it)
        details: Additional context information
        timestamp: Timestamp in ISO format
    """
    # Create logs directory
    log_dir = os.path.join(os.getcwd(), "logs", "client")
    os.makedirs(log_dir, exist_ok=True)
    
    # Format timestamp
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    # Format log entry
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "source": source,
        "message": message,
        "details": details or {}
    }
    
    # Get log file path
    today = datetime.now().strftime("%Y-%m-%d")
    client_log_file = os.path.join(log_dir, f"client_{today}.log")
    
    # Write log to file
    try:
        with open(client_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logging.error(f"Error writing client log to file: {str(e)}")

def get_client_logs(
    limit: int = 100,
    level: Optional[str] = None,
    source: Optional[str] = None
) -> list:
    """
    Retrieve client logs with optional filtering.
    
    Args:
        limit: Maximum number of logs to return
        level: Filter by log level
        source: Filter by log source
        
    Returns:
        List of log entries
    """
    try:
        logs = []
        log_dir = os.path.join(os.getcwd(), "logs", "client")
        
        if not os.path.exists(log_dir):
            return logs
        
        # Get log files (reverse chronological order)
        log_files = sorted(
            [f for f in os.listdir(log_dir) if f.startswith("client_")],
            reverse=True
        )
        
        # Process each log file
        for log_file in log_files:
            file_path = os.path.join(log_dir, log_file)
            
            with open(file_path, "r") as f:
                lines = f.readlines()
                
                # Process lines in reverse (newest first)
                for line in reversed(lines):
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if level and entry.get("level") != level:
                            continue
                            
                        if source and entry.get("source") != source:
                            continue
                        
                        # Add to logs
                        logs.append(entry)
                        
                        # Check limit
                        if len(logs) >= limit:
                            return logs
                    except:
                        # Skip invalid lines
                        continue
        
        return logs
        
    except Exception as e:
        logging.error(f"Error retrieving client logs: {str(e)}")
        return [] 