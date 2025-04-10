"""
Logging utility for handling application logging with context tracking and performance metrics.
"""

import logging
import logging.handlers
import os
import time
import json
import traceback
import threading
import uuid
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from .config import config

class ContextTracker:
    """Track request context for structured logging."""
    
    _local = threading.local()
    
    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """Get the current request context.
        
        Returns:
            Dict containing the current request context
        """
        if not hasattr(cls._local, "context"):
            cls._local.context = {"request_id": str(uuid.uuid4())}
        return cls._local.context
    
    @classmethod
    def set_context(cls, **kwargs) -> None:
        """Set context values for the current request.
        
        Args:
            **kwargs: Key-value pairs to add to the context
        """
        context = cls.get_context()
        context.update(kwargs)
    
    @classmethod
    def add_context(cls, **kwargs) -> None:
        """Add additional context values for the current request.
        Alias for set_context for better semantic clarity.
        
        Args:
            **kwargs: Key-value pairs to add to the context
        """
        cls.set_context(**kwargs)
    
    @classmethod
    def clear_context(cls) -> None:
        """Clear the current request context."""
        if hasattr(cls._local, "context"):
            delattr(cls._local, "context")

class StructuredLogRecord(logging.LogRecord):
    """Extended LogRecord with structured data support."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with standard LogRecord arguments."""
        super().__init__(*args, **kwargs)
        # Add context to the log record
        self.context = ContextTracker.get_context()
        
        # Add additional useful fields
        self.timestamp = datetime.now().isoformat()
        self.app_name = config.app_name
        self.environment = config.environment

class StructuredJsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: StructuredLogRecord) -> str:
        """Format record as JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": record.timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "app_name": record.app_name,
            "environment": record.environment,
        }
        
        # Add context data directly to the log object for flatter structure
        for key, value in record.context.items():
            log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, "extra") and record.extra:
            log_data["extra"] = record.extra
        
        return json.dumps(log_data)

class AppLogger:
    """Application logger class with context tracking and performance metrics."""
    
    def __init__(self, name: str = "app"):
        """Initialize logger.
        
        Args:
            name: Logger name
        """
        # Use our custom LogRecord factory
        logging.setLogRecordFactory(StructuredLogRecord)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(config.logging.level)
        
        # Remove existing handlers to avoid duplicates when reloading
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Create formatters
        json_formatter = StructuredJsonFormatter()
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(name)s] %(message)s"
        )
        
        # Create file handler
        log_dir = os.path.dirname(config.logging.file)
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            config.logging.file,
            maxBytes=config.logging.max_size,
            backupCount=config.logging.backup_count
        )
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(config.logging.level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(config.logging.level)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Performance metrics tracking
        self._timers = {}
    
    def _log(self, level: int, message: str, *args, **kwargs) -> None:
        """Log a message with the specified level.
        
        Args:
            level: Log level
            message: Log message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        extra = kwargs.pop("extra", {})
        self.logger.log(level, message, *args, extra={"extra": extra}, **kwargs)
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message.
        
        Args:
            message: Log message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self._log(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message.
        
        Args:
            message: Log message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self._log(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message.
        
        Args:
            message: Log message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self._log(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message.
        
        Args:
            message: Log message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self._log(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message.
        
        Args:
            message: Log message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self._log(logging.CRITICAL, message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception message.
        
        Args:
            message: Log message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self._log(logging.ERROR, message, exc_info=True, *args, **kwargs)
    
    def set_context(self, **kwargs) -> None:
        """Set context values for the current request.
        
        Args:
            **kwargs: Key-value pairs to add to the context
        """
        ContextTracker.set_context(**kwargs)
    
    def add_context(self, **kwargs) -> None:
        """Add additional context values for the current request.
        Alias for set_context for better semantic clarity.
        
        Args:
            **kwargs: Key-value pairs to add to the context
        """
        ContextTracker.add_context(**kwargs)
    
    def clear_context(self) -> None:
        """Clear the current request context."""
        ContextTracker.clear_context()
    
    def start_timer(self, name: str) -> None:
        """Start a performance timer.
        
        Args:
            name: Timer name
        """
        self._timers[name] = time.time()
        self.debug(f"Timer '{name}' started")
    
    def stop_timer(self, name: str) -> float:
        """Stop a performance timer and log the elapsed time.
        
        Args:
            name: Timer name
            
        Returns:
            Elapsed time in milliseconds
            
        Raises:
            KeyError: If the timer was not started
        """
        if name not in self._timers:
            self.warning(f"Timer '{name}' was not started")
            return 0
        
        elapsed = (time.time() - self._timers.pop(name)) * 1000  # Convert to ms
        self.debug(
            f"Timer '{name}' stopped", 
            extra={
                "performance": {
                    "timer_name": name,
                    "elapsed_ms": elapsed
                }
            }
        )
        return elapsed
    
    def log_metric(self, name: str, value: Union[int, float], unit: str = "") -> None:
        """Log a performance or business metric.
        
        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement (optional)
        """
        self.info(
            f"Metric: {name}={value}{unit}",
            extra={
                "metric": {
                    "name": name,
                    "value": value,
                    "unit": unit
                }
            }
        )
    
    def log_request(self, method: str, path: str, status_code: int, elapsed_ms: float) -> None:
        """Log HTTP request details.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            elapsed_ms: Request processing time in milliseconds
        """
        self.info(
            f"{method} {path} {status_code} {elapsed_ms:.2f}ms",
            extra={
                "http_request": {
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "elapsed_ms": elapsed_ms
                }
            }
        )
    
    def log_batch_operation(self, operation: str, total: int, success: int, failed: int) -> None:
        """Log batch operation details.
        
        Args:
            operation: Operation name
            total: Total number of items
            success: Number of successful items
            failed: Number of failed items
        """
        self.info(
            f"Batch {operation}: {success}/{total} successful, {failed} failed",
            extra={
                "batch_operation": {
                    "operation": operation,
                    "total": total,
                    "success": success,
                    "failed": failed
                }
            }
        )

def configure_logger(log_level: str = "INFO", log_file: str = "app.log") -> None:
    """Configure the global logger with custom settings.
    Used primarily for testing or custom initialization.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    """
    # Get the numeric log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Override config settings for logging
    config.logging.level = level
    config.logging.file = log_file
    
    # Re-initialize the default logger
    global logger
    logger = AppLogger()

def get_logger(name: str) -> AppLogger:
    """Get a logger instance for the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        AppLogger instance
    """
    return AppLogger(name)

# Create default logger instance
logger = AppLogger() 