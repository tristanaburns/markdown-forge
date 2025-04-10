"""
Error handling module for Markdown Forge.

This module provides centralized error handling with retry mechanisms
for the application.
"""

import functools
import time
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from fastapi import HTTPException, status
from pydantic import BaseModel

from .logger import error_logger, log_function_call

# Type variable for generic return type
T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    code: str
    message: str
    details: Optional[str] = None


class MarkdownForgeError(Exception):
    """Base exception class for Markdown Forge."""
    
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR", 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[str] = None
    ):
        """
        Initialize the error.
        
        Args:
            message: Human-readable error message
            code: Error code for identification
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)
    
    def to_response(self) -> ErrorResponse:
        """
        Convert the error to a response model.
        
        Returns:
            ErrorResponse: The error response
        """
        return ErrorResponse(
            code=self.code,
            message=self.message,
            details=self.details,
        )
    
    def to_http_exception(self) -> HTTPException:
        """
        Convert the error to an HTTP exception.
        
        Returns:
            HTTPException: The HTTP exception
        """
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_response().dict(),
        )


class ValidationError(MarkdownForgeError):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize the validation error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class NotFoundError(MarkdownForgeError):
    """Exception for not found errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize the not found error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class AuthenticationError(MarkdownForgeError):
    """Exception for authentication errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize the authentication error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationError(MarkdownForgeError):
    """Exception for authorization errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize the authorization error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConversionError(MarkdownForgeError):
    """Exception for conversion errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize the conversion error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            code="CONVERSION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class FileOperationError(MarkdownForgeError):
    """Exception for file operation errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize the file operation error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            code="FILE_OPERATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


def handle_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle errors in functions.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except MarkdownForgeError:
            # Re-raise MarkdownForgeError exceptions
            raise
        except Exception as e:
            # Log the error
            error_logger.error(
                f"Unexpected error in {func.__name__}",
                extra={
                    "function": func.__name__,
                    "error": str(e),
                },
                exc_info=True,
            )
            
            # Raise a generic error
            raise MarkdownForgeError(
                message=f"An unexpected error occurred: {str(e)}",
                details=str(e),
            )
    
    return wrapper


def handle_async_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle errors in async functions.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except MarkdownForgeError:
            # Re-raise MarkdownForgeError exceptions
            raise
        except Exception as e:
            # Log the error
            error_logger.error(
                f"Unexpected error in {func.__name__}",
                extra={
                    "function": func.__name__,
                    "error": str(e),
                },
                exc_info=True,
            )
            
            # Raise a generic error
            raise MarkdownForgeError(
                message=f"An unexpected error occurred: {str(e)}",
                details=str(e),
            )
    
    return wrapper


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
) -> Callable:
    """
    Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Backoff multiplier
        exceptions: Exception(s) to catch and retry on
        
    Returns:
        The decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Convert single exception to list
            if not isinstance(exceptions, list):
                exception_types = [exceptions]
            else:
                exception_types = exceptions
            
            # Initialize variables
            attempt = 1
            current_delay = delay
            
            # Retry loop
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except tuple(exception_types) as e:
                    # Check if this is the last attempt
                    if attempt == max_attempts:
                        error_logger.error(
                            f"Failed after {max_attempts} attempts",
                            extra={
                                "function": func.__name__,
                                "error": str(e),
                                "attempt": attempt,
                            },
                            exc_info=True,
                        )
                        raise
                    
                    # Log retry attempt
                    error_logger.warning(
                        f"Attempt {attempt} failed, retrying in {current_delay} seconds",
                        extra={
                            "function": func.__name__,
                            "error": str(e),
                            "attempt": attempt,
                            "next_attempt": attempt + 1,
                            "delay": current_delay,
                        },
                    )
                    
                    # Wait before retrying
                    time.sleep(current_delay)
                    
                    # Increase delay for next attempt
                    current_delay *= backoff
                    attempt += 1
        
        return wrapper
    
    return decorator


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
) -> Callable:
    """
    Decorator to retry an async function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Backoff multiplier
        exceptions: Exception(s) to catch and retry on
        
    Returns:
        The decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Convert single exception to list
            if not isinstance(exceptions, list):
                exception_types = [exceptions]
            else:
                exception_types = exceptions
            
            # Initialize variables
            attempt = 1
            current_delay = delay
            
            # Retry loop
            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except tuple(exception_types) as e:
                    # Check if this is the last attempt
                    if attempt == max_attempts:
                        error_logger.error(
                            f"Failed after {max_attempts} attempts",
                            extra={
                                "function": func.__name__,
                                "error": str(e),
                                "attempt": attempt,
                            },
                            exc_info=True,
                        )
                        raise
                    
                    # Log retry attempt
                    error_logger.warning(
                        f"Attempt {attempt} failed, retrying in {current_delay} seconds",
                        extra={
                            "function": func.__name__,
                            "error": str(e),
                            "attempt": attempt,
                            "next_attempt": attempt + 1,
                            "delay": current_delay,
                        },
                    )
                    
                    # Wait before retrying
                    await asyncio.sleep(current_delay)
                    
                    # Increase delay for next attempt
                    current_delay *= backoff
                    attempt += 1
        
        return wrapper
    
    return decorator


# Import asyncio for async retry
import asyncio

# Export error classes and functions
__all__ = [
    "ErrorResponse",
    "MarkdownForgeError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ConversionError",
    "FileOperationError",
    "handle_errors",
    "handle_async_errors",
    "retry",
    "retry_async",
] 