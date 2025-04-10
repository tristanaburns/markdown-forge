"""
Error handling utility for Markdown Forge.
This module provides centralized error handling for the application.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Dict, Optional
import logging
import traceback

# Configure logging
logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception class for application errors."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        """
        Initialize application error.
        
        Args:
            status_code (int): HTTP status code
            message (str): Error message
            details (str, optional): Additional error details
            error_code (str, optional): Error code for client handling
        """
        self.status_code = status_code
        self.message = message
        self.details = details
        self.error_code = error_code
        super().__init__(message)

class AuthenticationError(AppError):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[str] = None):
        """
        Initialize authentication error.
        
        Args:
            message (str): Error message
            details (str, optional): Additional error details
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            details=details,
            error_code="AUTH_ERROR"
        )

class AuthorizationError(AppError):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Permission denied", details: Optional[str] = None):
        """
        Initialize authorization error.
        
        Args:
            message (str): Error message
            details (str, optional): Additional error details
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            details=details,
            error_code="AUTHZ_ERROR"
        )

class NotFoundError(AppError):
    """Exception for resource not found errors."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[str] = None):
        """
        Initialize not found error.
        
        Args:
            message (str): Error message
            details (str, optional): Additional error details
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            details=details,
            error_code="NOT_FOUND"
        )

class ValidationError(AppError):
    """Exception for validation errors."""
    
    def __init__(self, message: str = "Validation error", details: Optional[str] = None):
        """
        Initialize validation error.
        
        Args:
            message (str): Error message
            details (str, optional): Additional error details
        """
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            details=details,
            error_code="VALIDATION_ERROR"
        )

class ConversionError(AppError):
    """Exception for file conversion errors."""
    
    def __init__(self, message: str = "Conversion failed", details: Optional[str] = None):
        """
        Initialize conversion error.
        
        Args:
            message (str): Error message
            details (str, optional): Additional error details
        """
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            details=details,
            error_code="CONVERSION_ERROR"
        )

class RateLimitError(AppError):
    """Exception for rate limit errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[str] = None):
        """
        Initialize rate limit error.
        
        Args:
            message (str): Error message
            details (str, optional): Additional error details
        """
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            details=details,
            error_code="RATE_LIMIT_ERROR"
        )

def register_error_handlers(app: FastAPI) -> None:
    """
    Register error handlers for the FastAPI application.
    
    Args:
        app (FastAPI): FastAPI application
    """
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """
        Handle application errors.
        
        Args:
            request (Request): FastAPI request
            exc (AppError): Application error
            
        Returns:
            JSONResponse: Error response
        """
        logger.error(f"Application error: {exc.message}", exc_info=True)
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle validation errors.
        
        Args:
            request (Request): FastAPI request
            exc (RequestValidationError): Validation error
            
        Returns:
            JSONResponse: Error response
        """
        logger.error(f"Validation error: {exc.errors()}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """
        Handle database errors.
        
        Args:
            request (Request): FastAPI request
            exc (SQLAlchemyError): Database error
            
        Returns:
            JSONResponse: Error response
        """
        logger.error(f"Database error: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "DATABASE_ERROR",
                "message": "Database error",
                "details": str(exc)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle general errors.
        
        Args:
            request (Request): FastAPI request
            exc (Exception): Exception
            
        Returns:
            JSONResponse: Error response
        """
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": str(exc)
            }
        ) 