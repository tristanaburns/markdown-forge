"""
Error handling utilities for the Markdown Forge application.
Provides centralized error handling and custom exception classes.
"""

import traceback
import logging
from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

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