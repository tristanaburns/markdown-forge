"""
Route helper utilities for Flask application.
Provides decorators and utilities for consistent route handling.
"""

import functools
import time
from typing import Callable, Dict, Any, Optional
from flask import request, render_template, session

from .logger import get_logger

logger = get_logger(__name__)

def track_performance(page_name: str = None):
    """
    Decorator for tracking performance metrics of route handlers.
    
    Args:
        page_name: Name of the page/route to use in metrics. Defaults to route path.
    
    Returns:
        Decorated function with performance tracking
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine page name
            route_name = page_name or request.path
            
            # Set context for logging
            user_id = session.get('user_id', 'anonymous')
            logger.set_context(page=route_name, user_id=user_id)
            
            # Start timer
            timer_key = f"{route_name}_render"
            logger.start_timer(timer_key)
            logger.info(f"Accessing {route_name} page")
            
            try:
                # Execute the route handler
                result = func(*args, **kwargs)
                
                # Log success
                elapsed = logger.stop_timer(timer_key)
                logger.log_metric(f"{route_name}_render_time", elapsed, "ms")
                logger.debug(f"Successfully rendered {route_name}", extra={"status": "success"})
                
                return result
            except Exception as e:
                # Log failure
                elapsed = logger.stop_timer(timer_key)
                logger.log_metric(f"{route_name}_error_time", elapsed, "ms")
                logger.exception(f"Error in route {route_name}: {str(e)}")
                
                # Return error page
                return render_template('error.html', message=f"An error occurred: {str(e)}"), 500
            finally:
                # Always clear context
                logger.clear_context()
                
        return wrapper
    return decorator

def api_request(url: str, method: str = 'GET', params: Optional[Dict[str, Any]] = None, 
                json_data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None):
    """
    Helper function to make API requests with proper error handling and logging.
    
    Args:
        url: The API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        params: Query parameters for the request
        json_data: JSON data for the request body
        headers: HTTP headers for the request
        
    Returns:
        API response or None if request failed
    """
    import requests
    
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    logger.debug(f"Making API request", extra={
        "request_id": request_id,
        "url": url,
        "method": method
    })
    
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=headers
        )
        
        elapsed = (time.time() - start_time) * 1000
        logger.log_metric(f"api_request_time", elapsed, "ms")
        
        logger.debug(f"API request completed", extra={
            "request_id": request_id,
            "status": response.status_code,
            "elapsed_ms": elapsed
        })
        
        return response
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        logger.error(f"API request failed", extra={
            "request_id": request_id,
            "error": str(e),
            "elapsed_ms": elapsed
        })
        
        return None 