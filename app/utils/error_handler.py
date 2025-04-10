"""
Error handling utilities for the Markdown Forge application.
Provides centralized error handling and custom exception classes.
"""

import traceback
import logging
from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from typing import Dict, Optional

# Configure logger
logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception class for application errors."""
    
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert exception to dictionary for JSON response."""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

class ValidationError(AppError):
    """Exception raised for validation errors."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)

class NotFoundError(AppError):
    """Exception raised when a resource is not found."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=404, payload=payload)

class ConversionError(AppError):
    """Exception raised when file conversion fails."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=500, payload=payload)

class AuthenticationError(AppError):
    """Exception raised for authentication errors."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=401, payload=payload)

class AuthorizationError(AppError):
    """Exception raised for authorization errors."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=403, payload=payload)

class RateLimitError(AppError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=429, payload=payload)

class ApiError(Exception):
    """Exception raised for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int,
        data: Optional[Dict] = None
    ):
        """Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            data: Additional error data
        """
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict:
        """Convert error to dictionary.
        
        Returns:
            Error data as dictionary
        """
        return {
            'message': self.message,
            'status_code': self.status_code,
            'data': self.data
        }

class UiError(Exception):
    """Exception raised for UI-specific errors."""
    
    def __init__(
        self,
        message: str,
        component: str,
        data: Optional[Dict] = None
    ):
        """Initialize UI error.
        
        Args:
            message: Error message
            component: UI component where error occurred
            data: Additional error data
        """
        self.message = message
        self.component = component
        self.data = data or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict:
        """Convert error to dictionary.
        
        Returns:
            Error data as dictionary
        """
        return {
            'message': self.message,
            'component': self.component,
            'data': self.data
        }

def register_error_handlers(app):
    """Register error handlers with the Flask application."""
    
    @app.errorhandler(AppError)
    def handle_app_error(error):
        """Handle application-specific errors."""
        # Log the error
        logger.error(f"Application Error: {error.message}")
        if error.payload:
            logger.error(f"Error payload: {error.payload}")
        
        if request.path.startswith('/api/'):
            # API requests return JSON
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
            return response
        else:
            # Web requests return HTML
            return render_template('errors/500.html'), error.status_code
    
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        """Handle Werkzeug HTTP exceptions."""
        # Log the error
        logger.error(f"HTTP Error: {error.code} - {error.description}")
        
        if request.path.startswith('/api/'):
            # API requests return JSON
            response = jsonify({
                'message': error.description,
                'status_code': error.code
            })
            response.status_code = error.code
            return response
        else:
            # Web requests return HTML
            return render_template('errors/500.html'), error.code
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        # Log the error
        logger.error(f"404 Not Found: {request.path}")
        
        if request.path.startswith('/api/'):
            # API requests return JSON
            response = jsonify({
                'message': 'Resource not found',
                'status_code': 404
            })
            response.status_code = 404
            return response
        else:
            # Web requests return HTML
            return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        # Log the error
        logger.error(f"Internal Server Error: {error}")
        logger.error(traceback.format_exc())
        
        if request.path.startswith('/api/'):
            # API requests return JSON
            response = jsonify({
                'message': 'Internal server error',
                'status_code': 500
            })
            response.status_code = 500
            return response
        else:
            # Web requests return HTML
            return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        # Log the error
        logger.error(f"Unexpected Error: {error}")
        logger.error(traceback.format_exc())
        
        if request.path.startswith('/api/'):
            # API requests return JSON
            response = jsonify({
                'message': 'An unexpected error occurred',
                'status_code': 500
            })
            response.status_code = 500
            return response
        else:
            # Web requests return HTML
            return render_template('errors/500.html'), 500

def handle_api_error(error: ApiError) -> Dict:
    """Handle API error and return user-friendly message.
    
    Args:
        error: API error to handle
        
    Returns:
        User-friendly error message
    """
    if error.status_code == 400:
        return {
            'type': 'warning',
            'message': 'Invalid request. Please check your input.',
            'details': error.message
        }
    elif error.status_code == 401:
        return {
            'type': 'error',
            'message': 'Authentication required. Please log in.',
            'details': error.message
        }
    elif error.status_code == 403:
        return {
            'type': 'error',
            'message': 'Access denied. You do not have permission.',
            'details': error.message
        }
    elif error.status_code == 404:
        return {
            'type': 'warning',
            'message': 'Resource not found.',
            'details': error.message
        }
    elif error.status_code == 429:
        return {
            'type': 'warning',
            'message': 'Too many requests. Please try again later.',
            'details': error.message
        }
    elif error.status_code >= 500:
        return {
            'type': 'error',
            'message': 'Server error. Please try again later.',
            'details': error.message
        }
    else:
        return {
            'type': 'error',
            'message': 'An unexpected error occurred.',
            'details': error.message
        }

def handle_ui_error(error: UiError) -> Dict:
    """Handle UI error and return user-friendly message.
    
    Args:
        error: UI error to handle
        
    Returns:
        User-friendly error message
    """
    return {
        'type': 'error',
        'message': error.message,
        'component': error.component,
        'details': error.data.get('details', '')
    } 