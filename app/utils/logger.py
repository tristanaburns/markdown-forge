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
import inspect
import functools
import sys
from typing import Optional, Dict, Any, List, Union, Callable
from datetime import datetime
from .config import config
from pathlib import Path

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
        frame = inspect.currentframe().f_back.f_back
        self.function_name = frame.f_code.co_name
        self.module_name = frame.f_code.co_filename
        self.line_number = frame.f_lineno
        # Don't set any custom attributes on the LogRecord itself

class StructuredJsonFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after parsing the log record."""
    
    def format(self, record: StructuredLogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module_name,
            'function': record.function_name,
            'line': record.line_number
        }
        
        # Add the custom data if available
        if hasattr(record, 'data'):
            log_data.update(record.data)
        
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data)

class AppLogger:
    """Application logger class with context tracking and performance metrics."""
    
    def __init__(self, name: str, log_file: Optional[str] = None, level: str = 'INFO'):
        """Initialize logger.
        
        Args:
            name: Logger name
            log_file: Path to log file
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Set custom record factory
        logging.setLogRecordFactory(StructuredLogRecord)
        
        # Console handler with structured formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredJsonFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler if log_file specified
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredJsonFormatter())
            self.logger.addHandler(file_handler)
        
        # Performance metrics tracking
        self._timers = {}
        
        # Function call tracking
        self._call_stack = []
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log an exception with traceback.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        # Get the stack trace
        stack_trace = traceback.format_stack()
        
        # Add stack trace to kwargs
        data = kwargs.get('data', {})
        data['stack_trace'] = stack_trace
        kwargs['data'] = data
        
        # Log the error with the current exception info
        self.logger.error(message, exc_info=True, extra=kwargs)
    
    def set_context(self, **kwargs) -> None:
        """Set context values for the current request.
        
        Args:
            **kwargs: Key-value pairs to add to the context
        """
        ContextTracker.set_context(**kwargs)
    
    def add_context(self, **kwargs) -> None:
        """Add additional context values for the current request.
        
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
            name: Name of the timer
        """
        self._timers[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """Stop a performance timer and return the elapsed time.
        
        Args:
            name: Name of the timer
            
        Returns:
            Elapsed time in seconds
        """
        if name not in self._timers:
            return 0.0
        
        elapsed = time.time() - self._timers[name]
        del self._timers[name]
        return elapsed
    
    def log_metric(self, name: str, value: float, unit: str = "ms") -> None:
        """Log a performance metric.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            unit: Unit of the metric
        """
        self.logger.info(
            f"Metric: {name} = {value} {unit}",
            extra={"metric": {"name": name, "value": value, "unit": unit}}
        )
    
    def log_function_entry(self, func_name: str, params: Dict[str, Any], request_id: Optional[str] = None) -> None:
        """Log function entry with parameters"""
        self.logger.debug(
            f"Entering function: {func_name}",
            extra={
                'data': {
                    'event_type': 'entry',
                    'params': params,
                    'request_id': request_id
                }
            }
        )
    
    def log_function_exit(self, func_name: str, result: Any, execution_time: float, request_id: Optional[str] = None) -> None:
        """Log function exit with return value and performance metrics"""
        self.logger.debug(
            f"Exiting function: {func_name}",
            extra={
                'data': {
                    'event_type': 'exit',
                    'return_value': str(result),
                    'performance': {
                        'execution_time_ms': execution_time * 1000
                    },
                    'request_id': request_id
                }
            }
        )
    
    def log_function_error(self, func_name: str, error: Exception, request_id: Optional[str] = None) -> None:
        """Log function errors with full stack trace"""
        self.logger.error(
            f"Error in function: {func_name}",
            exc_info=error,
            extra={
                'data': {
                    'event_type': 'error',
                    'request_id': request_id
                }
            }
        )

def log_function(logger: AppLogger) -> Callable:
    """Decorator to automatically log function entry, exit, and exceptions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            import uuid
            
            func_name = func.__name__
            # Generate request ID for tracking
            request_id = str(uuid.uuid4())
            
            # Prepare parameters for logging
            params = {
                'args': [str(arg) for arg in args],
                'kwargs': {k: str(v) for k, v in kwargs.items()}
            }
            
            try:
                # Log function entry
                logger.log_function_entry(func_name, params, request_id)
                
                # Execute function and measure time
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful exit
                logger.log_function_exit(func_name, result, execution_time, request_id)
                
                return result
            except Exception as e:
                # Log error with full stack trace
                logger.log_function_error(func_name, e, request_id)
                raise
                
        return wrapper
    return decorator

def get_logger(name: str = "app") -> AppLogger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return AppLogger(name)

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
    logger = AppLogger(name="app", log_file=log_file, level=log_level) 