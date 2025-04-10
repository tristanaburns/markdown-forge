"""
Rate limiter utility for Markdown Forge.
This module provides rate limiting functionality for API endpoints.
"""

import time
from functools import wraps
from typing import Dict, Tuple, Callable
from fastapi import HTTPException, status, Request
import logging

# Configure logging
logger = logging.getLogger(__name__)

# In-memory storage for rate limiting
# Format: {(endpoint, ip): [(timestamp, count), ...]}
rate_limit_storage: Dict[Tuple[str, str], list] = {}

def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Rate limiting decorator for API endpoints.
    
    Args:
        max_requests (int): Maximum number of requests allowed in the time window
        window_seconds (int): Time window in seconds
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request object from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if not request:
                # If no request object found, proceed without rate limiting
                logger.warning("Rate limiting requested but no Request object found")
                return await func(*args, **kwargs)
            
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            
            # Get endpoint name
            endpoint = f"{func.__module__}.{func.__name__}"
            
            # Check rate limit
            current_time = time.time()
            key = (endpoint, client_ip)
            
            # Initialize or clean up old entries
            if key not in rate_limit_storage:
                rate_limit_storage[key] = []
            
            # Remove entries outside the time window
            rate_limit_storage[key] = [
                (ts, count) for ts, count in rate_limit_storage[key]
                if current_time - ts < window_seconds
            ]
            
            # Count requests in the current window
            total_requests = sum(count for _, count in rate_limit_storage[key])
            
            # Check if rate limit exceeded
            if total_requests >= max_requests:
                logger.warning(f"Rate limit exceeded for {endpoint} from {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
            
            # Add current request
            rate_limit_storage[key].append((current_time, 1))
            
            # Proceed with the request
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator 