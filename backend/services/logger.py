"""
Logging module for Markdown Forge.

This module provides structured JSON logging with appropriate log levels
and formatting for the application.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

# Configure logging directory
LOG_DIR = Path("/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file paths
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
ACCESS_LOG_FILE = LOG_DIR / "access.log"

# Configure logging format
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if available
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


# Configure app logger
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.INFO)

# File handler for app logs
app_file_handler = logging.FileHandler(APP_LOG_FILE)
app_file_handler.setFormatter(JSONFormatter())
app_logger.addHandler(app_file_handler)

# Console handler for app logs
app_console_handler = logging.StreamHandler(sys.stdout)
app_console_handler.setFormatter(JSONFormatter())
app_logger.addHandler(app_console_handler)

# Configure error logger
error_logger = logging.getLogger("error")
error_logger.setLevel(logging.ERROR)

# File handler for error logs
error_file_handler = logging.FileHandler(ERROR_LOG_FILE)
error_file_handler.setFormatter(JSONFormatter())
error_logger.addHandler(error_file_handler)

# Console handler for error logs
error_console_handler = logging.StreamHandler(sys.stderr)
error_console_handler.setFormatter(JSONFormatter())
error_logger.addHandler(error_console_handler)

# Configure access logger
access_logger = logging.getLogger("access")
access_logger.setLevel(logging.INFO)

# File handler for access logs
access_file_handler = logging.FileHandler(ACCESS_LOG_FILE)
access_file_handler.setFormatter(JSONFormatter())
access_logger.addHandler(access_file_handler)

# Console handler for access logs
access_console_handler = logging.StreamHandler(sys.stdout)
access_console_handler.setFormatter(JSONFormatter())
access_logger.addHandler(access_console_handler)


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function calls with parameters and return values.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get function name and module
        func_name = func.__name__
        module_name = func.__module__
        
        # Log function entry
        app_logger.debug(
            f"Entering function: {func_name}",
            extra={
                "function": func_name,
                "module": module_name,
                "args": str(args),
                "kwargs": str(kwargs),
            },
        )
        
        # Record start time
        start_time = time.time()
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log function exit
            app_logger.debug(
                f"Exiting function: {func_name}",
                extra={
                    "function": func_name,
                    "module": module_name,
                    "execution_time": execution_time,
                    "result": str(result),
                },
            )
            
            return result
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log function error
            error_logger.error(
                f"Error in function: {func_name}",
                extra={
                    "function": func_name,
                    "module": module_name,
                    "execution_time": execution_time,
                    "error": str(e),
                },
                exc_info=True,
            )
            
            # Re-raise the exception
            raise
    
    return wrapper


def log_api_request(func: Callable) -> Callable:
    """
    Decorator to log API requests with parameters and response.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get function name and module
        func_name = func.__name__
        module_name = func.__module__
        
        # Extract request information if available
        request_info = {}
        for arg in args:
            if hasattr(arg, "method") and hasattr(arg, "url"):
                request_info = {
                    "method": arg.method,
                    "url": str(arg.url),
                    "client": arg.client.host if hasattr(arg, "client") else None,
                    "headers": dict(arg.headers) if hasattr(arg, "headers") else None,
                }
                break
        
        # Log API request
        access_logger.info(
            f"API Request: {func_name}",
            extra={
                "function": func_name,
                "module": module_name,
                "request": request_info,
                "args": str(args),
                "kwargs": str(kwargs),
            },
        )
        
        # Record start time
        start_time = time.time()
        
        try:
            # Call the function
            result = await func(*args, **kwargs)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log API response
            access_logger.info(
                f"API Response: {func_name}",
                extra={
                    "function": func_name,
                    "module": module_name,
                    "execution_time": execution_time,
                    "status_code": getattr(result, "status_code", None),
                    "response": str(result),
                },
            )
            
            return result
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log API error
            error_logger.error(
                f"API Error: {func_name}",
                extra={
                    "function": func_name,
                    "module": module_name,
                    "execution_time": execution_time,
                    "error": str(e),
                },
                exc_info=True,
            )
            
            # Re-raise the exception
            raise
    
    return wrapper


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        The logger
    """
    return logging.getLogger(name)


# Export loggers
__all__ = [
    "app_logger",
    "error_logger",
    "access_logger",
    "log_function_call",
    "log_api_request",
    "get_logger",
] 