"""
Conversion error handler for Markdown Forge.
This module provides specialized error handling for file conversion operations.
"""

import logging
import traceback
import time
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class ConversionErrorType(Enum):
    """Types of conversion errors."""
    INPUT_VALIDATION = "input_validation"
    FORMAT_VALIDATION = "format_validation"
    TEMPLATE_ERROR = "template_error"
    PANDOC_ERROR = "pandoc_error"
    FILE_SYSTEM_ERROR = "file_system_error"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    MEMORY_ERROR = "memory_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"

class RecoveryStrategy(Enum):
    """Available recovery strategies for conversion errors."""
    RETRY_WITH_TIMEOUT_INCREASE = "retry_with_timeout_increase"
    RETRY_WITH_SIMPLIFIED_OPTIONS = "retry_with_simplified_options"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    RETRY_WITH_MEMORY_OPTIMIZATION = "retry_with_memory_optimization"
    RETRY_WITH_NETWORK_RETRY = "retry_with_network_retry"
    FALLBACK_TO_ALTERNATIVE_CONVERTER = "fallback_to_alternative_converter"

class ConversionError(Exception):
    """Exception raised for conversion errors."""
    
    def __init__(
        self, 
        message: str, 
        error_type: ConversionErrorType = ConversionErrorType.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
        recovery_attempts: int = 0,
        recovery_strategy: Optional[RecoveryStrategy] = None
    ):
        """
        Initialize a conversion error.
        
        Args:
            message: Human-readable error message
            error_type: Type of conversion error
            details: Additional error details
            status_code: HTTP status code
            recovery_attempts: Number of recovery attempts made
            recovery_strategy: Strategy used for recovery
        """
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.status_code = status_code
        self.traceback = traceback.format_exc()
        self.recovery_attempts = recovery_attempts
        self.recovery_strategy = recovery_strategy
        self.timestamp = time.time()
        super().__init__(self.message)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.
        
        Returns:
            Dict[str, Any]: Error details as a dictionary
        """
        return {
            "code": self.error_type.value,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code,
            "recovery_attempts": self.recovery_attempts,
            "recovery_strategy": self.recovery_strategy.value if self.recovery_strategy else None,
            "timestamp": self.timestamp
        }
        
    def log_error(self) -> None:
        """Log the error with appropriate level and details."""
        error_data = {
            "type": self.error_type.value,
            "message": self.message,
            "details": self.details,
            "traceback": self.traceback,
            "recovery_attempts": self.recovery_attempts,
            "recovery_strategy": self.recovery_strategy.value if self.recovery_strategy else None
        }
        
        if self.error_type in [
            ConversionErrorType.INPUT_VALIDATION,
            ConversionErrorType.FORMAT_VALIDATION
        ]:
            logger.warning(f"Conversion validation error: {self.message}", extra=error_data)
        else:
            logger.error(f"Conversion error: {self.message}", extra=error_data)
            
    def with_recovery_attempt(self, strategy: RecoveryStrategy) -> 'ConversionError':
        """
        Create a new error with an incremented recovery attempt count.
        
        Args:
            strategy: The recovery strategy to use
            
        Returns:
            ConversionError: A new error with incremented recovery attempts
        """
        return ConversionError(
            message=self.message,
            error_type=self.error_type,
            details=self.details,
            status_code=self.status_code,
            recovery_attempts=self.recovery_attempts + 1,
            recovery_strategy=strategy
        )

def handle_conversion_error(error: Exception) -> Dict[str, Any]:
    """
    Handle a conversion error and return a standardized response.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Dict[str, Any]: Standardized error response
    """
    if isinstance(error, ConversionError):
        error.log_error()
        return error.to_dict()
        
    # Handle other types of errors
    error_type = ConversionErrorType.UNKNOWN_ERROR
    status_code = 500
    details = {}
    
    if isinstance(error, FileNotFoundError):
        error_type = ConversionErrorType.FILE_SYSTEM_ERROR
        status_code = 404
        details = {"file_path": str(error)}
    elif isinstance(error, PermissionError):
        error_type = ConversionErrorType.PERMISSION_ERROR
        status_code = 403
    elif isinstance(error, TimeoutError):
        error_type = ConversionErrorType.TIMEOUT_ERROR
        status_code = 408
    elif isinstance(error, MemoryError):
        error_type = ConversionErrorType.MEMORY_ERROR
        status_code = 507  # Insufficient Storage
    elif isinstance(error, ConnectionError):
        error_type = ConversionErrorType.NETWORK_ERROR
        status_code = 503  # Service Unavailable
        
    conversion_error = ConversionError(
        message=str(error),
        error_type=error_type,
        details=details,
        status_code=status_code
    )
    
    conversion_error.log_error()
    return conversion_error.to_dict()

def is_recoverable_error(error: Exception) -> bool:
    """
    Check if an error is recoverable.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: True if the error is recoverable, False otherwise
    """
    if isinstance(error, ConversionError):
        return error.error_type in [
            ConversionErrorType.TIMEOUT_ERROR,
            ConversionErrorType.PANDOC_ERROR,
            ConversionErrorType.MEMORY_ERROR,
            ConversionErrorType.NETWORK_ERROR
        ]
        
    return isinstance(error, (TimeoutError, ConnectionError, MemoryError))

def get_error_recovery_strategy(error: Exception) -> Optional[RecoveryStrategy]:
    """
    Get a recovery strategy for an error.
    
    Args:
        error: The exception to get a recovery strategy for
        
    Returns:
        Optional[RecoveryStrategy]: Recovery strategy if available, None otherwise
    """
    if not is_recoverable_error(error):
        return None
        
    if isinstance(error, ConversionError):
        if error.error_type == ConversionErrorType.TIMEOUT_ERROR:
            return RecoveryStrategy.RETRY_WITH_TIMEOUT_INCREASE
        elif error.error_type == ConversionErrorType.PANDOC_ERROR:
            return RecoveryStrategy.RETRY_WITH_SIMPLIFIED_OPTIONS
        elif error.error_type == ConversionErrorType.MEMORY_ERROR:
            return RecoveryStrategy.RETRY_WITH_MEMORY_OPTIMIZATION
        elif error.error_type == ConversionErrorType.NETWORK_ERROR:
            return RecoveryStrategy.RETRY_WITH_NETWORK_RETRY
            
    if isinstance(error, TimeoutError):
        return RecoveryStrategy.RETRY_WITH_TIMEOUT_INCREASE
    elif isinstance(error, ConnectionError):
        return RecoveryStrategy.RETRY_WITH_NETWORK_RETRY
    elif isinstance(error, MemoryError):
        return RecoveryStrategy.RETRY_WITH_MEMORY_OPTIMIZATION
        
    return None

def apply_recovery_strategy(
    strategy: RecoveryStrategy, 
    func: Callable, 
    *args, 
    **kwargs
) -> Tuple[Any, Optional[ConversionError]]:
    """
    Apply a recovery strategy to a function.
    
    Args:
        strategy: The recovery strategy to apply
        func: The function to apply the strategy to
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Tuple[Any, Optional[ConversionError]]: Result of the function and any error that occurred
    """
    try:
        if strategy == RecoveryStrategy.RETRY_WITH_TIMEOUT_INCREASE:
            # Increase timeout for next attempt
            if 'timeout' in kwargs:
                kwargs['timeout'] = kwargs.get('timeout', 30) * 1.5
            time.sleep(1)  # Brief pause before retry
            
        elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            # Exponential backoff
            backoff_time = 2 ** kwargs.get('retry_count', 0)
            time.sleep(backoff_time)
            
        elif strategy == RecoveryStrategy.RETRY_WITH_MEMORY_OPTIMIZATION:
            # Reduce memory usage
            if 'chunk_size' in kwargs:
                kwargs['chunk_size'] = kwargs.get('chunk_size', 1024) // 2
                
        elif strategy == RecoveryStrategy.RETRY_WITH_NETWORK_RETRY:
            # Add network retry logic
            max_retries = kwargs.get('max_retries', 3)
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs), None
                except ConnectionError:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise
                        
        # Execute the function with the modified parameters
        return func(*args, **kwargs), None
        
    except Exception as e:
        # Handle any errors that occur during recovery
        if isinstance(e, ConversionError):
            return None, e
        else:
            error_response = handle_conversion_error(e)
            return None, ConversionError(
                message=error_response["message"],
                error_type=ConversionErrorType(error_response["code"]),
                details=error_response["details"],
                status_code=error_response["status_code"]
            ) 