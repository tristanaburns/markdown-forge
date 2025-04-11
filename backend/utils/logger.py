"""
Logging utility for the backend with enhanced visibility and structured logging.
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
from ..config import config

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
        self.thread_id = threading.get_ident()
        self.thread_name = threading.current_thread().name
        
        # Add function information if available
        frame = inspect.currentframe()
        if frame:
            try:
                # Get the caller's frame
                caller_frame = frame.f_back
                if caller_frame:
                    # Get function information
                    self.function_name = caller_frame.f_code.co_name
                    self.module_name = caller_frame.f_code.co_filename
                    self.line_number = caller_frame.f_lineno
            finally:
                # Always delete the frame to avoid memory leaks
                del frame

class StructuredJsonFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after parsing the log record."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        # Create a dict with the log record attributes
        log_data = {
            "timestamp": getattr(record, "timestamp", datetime.now().isoformat()),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": getattr(record, "module_name", record.module),
            "function": getattr(record, "function_name", record.funcName),
            "line": getattr(record, "line_number", record.lineno),
            "thread_id": getattr(record, "thread_id", threading.get_ident()),
            "thread_name": getattr(record, "thread_name", threading.current_thread().name),
            "app_name": getattr(record, "app_name", config.app_name),
            "environment": getattr(record, "environment", config.environment),
        }
        
        # Add context if available
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add the custom data if available
        if hasattr(record, 'data'):
            log_data.update(record.data)
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

class BackendLogger:
    """Backend logger class with context tracking and performance metrics."""
    
    def __init__(self, name: str = "backend"):
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
    
    def log_function_entry(self, func: Callable, *args, **kwargs) -> None:
        """Log function entry with parameters for enhanced debugging.
        
        Args:
            func: The function to log
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        # Extract function information
        func_name = func.__name__
        module_name = func.__module__
        
        # Process function arguments for logging
        params = {
            "args": [],
            "kwargs": {}
        }
        
        # Process positional arguments
        for arg in args:
            try:
                # Convert to string representation, limiting the size
                arg_str = str(arg)
                if len(arg_str) > 1000:
                    arg_str = arg_str[:1000] + "..."
                params["args"].append(arg_str)
            except Exception:
                params["args"].append("<non-serializable>")
        
        # Process keyword arguments
        for key, value in kwargs.items():
            try:
                # Convert to string representation, limiting the size
                value_str = str(value)
                if len(value_str) > 1000:
                    value_str = value_str[:1000] + "..."
                params["kwargs"][key] = value_str
            except Exception:
                params["kwargs"][key] = "<non-serializable>"
        
        # Generate a request ID for tracking this function call
        request_id = str(uuid.uuid4())
        
        # Add function to call stack with start time
        self._call_stack.append({
            "function": func_name,
            "module": module_name,
            "start_time": time.time(),
            "request_id": request_id
        })
        
        # Log the function entry
        self.logger.debug(
            f"Entering function: {module_name}.{func_name}",
            extra={
                'data': {
                    "event_type": "entry",
                    "params": params,
                    "request_id": request_id
                }
            }
        )
        
        return request_id
    
    def log_function_exit(self, func: Callable, return_value: Any = None) -> None:
        """Log function exit with return value and execution time.
        
        Args:
            func: The function to log
            return_value: The return value from the function
        """
        # Extract function information
        func_name = func.__name__
        module_name = func.__module__
        
        # Get the call info from the stack
        call_info = None
        for call in reversed(self._call_stack):
            if call["function"] == func_name and call["module"] == module_name:
                call_info = call
                self._call_stack.remove(call)
                break
        
        if not call_info:
            # No matching call found, just log with minimal info
            self.logger.debug(
                f"Exiting function: {module_name}.{func_name}",
                extra={
                    'data': {
                        "event_type": "exit",
                        "return_value": str(return_value)[:1000] if return_value is not None else None
                    }
                }
            )
            return
        
        # Calculate execution time
        end_time = time.time()
        execution_time = end_time - call_info["start_time"]
        execution_time_ms = execution_time * 1000
        
        # Process return value for logging
        if return_value is not None:
            try:
                # Convert to string representation, limiting the size
                return_value_str = str(return_value)
                if len(return_value_str) > 1000:
                    return_value_str = return_value_str[:1000] + "..."
            except Exception:
                return_value_str = "<non-serializable>"
        else:
            return_value_str = None
        
        # Log the function exit
        self.logger.debug(
            f"Exiting function: {module_name}.{func_name}",
            extra={
                'data': {
                    "event_type": "exit",
                    "return_value": return_value_str,
                    "performance": {
                        "execution_time_ms": execution_time_ms
                    },
                    "request_id": call_info["request_id"]
                }
            }
        )
    
    def log_step(self, step_name: str, details: Dict[str, Any] = None) -> None:
        """Log a step in the execution flow.
        
        Args:
            step_name: Name of the step
            details: Additional details about the step
        """
        self.logger.debug(
            f"Step: {step_name}",
            extra={
                "step": {
                    "name": step_name,
                    "details": details or {},
                    "call_stack": self._call_stack.copy()
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

def log_function(func: Callable) -> Callable:
    """Decorator for automatic function entry/exit and exception logging."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get the logger
        if hasattr(func, "__self__"):
            # Method on an object
            logger = get_logger(func.__self__.__class__.__name__)
        else:
            # Normal function
            logger = get_logger(func.__module__)
        
        try:
            # Log function entry
            request_id = logger.log_function_entry(func, *args, **kwargs)
            
            # Execute the function
            start_time = time.time()
            result = func(*args, **kwargs)
            
            # Log function exit
            logger.log_function_exit(func, result)
            
            return result
        except Exception as e:
            # Log the exception with custom attributes
            logger.logger.error(
                f"Error in function {func.__name__}: {str(e)}",
                exc_info=True,
                extra={
                    'data': {
                        "event_type": "error",
                        "function": func.__name__,
                        "module": func.__module__,
                        "error_type": e.__class__.__name__,
                        "error_message": str(e)
                    }
                }
            )
            raise
    
    return wrapper

def get_logger(name: str = "backend") -> BackendLogger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return BackendLogger(name)

def configure_logger(log_level: str = "INFO", log_file: str = "backend.log") -> None:
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
    logger = BackendLogger()

# Create default logger instance
logger = BackendLogger() 