import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from utils.logger import get_logger

logger = get_logger(__name__)

# OAuth2 password bearer scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Secret key for JWT tokens - in production, this should be secure and from environment
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development_secret_key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Demo users - in production, this would be stored in a database
DEMO_USERS = {
    "user@example.com": {
        "id": "user1",
        "username": "user@example.com",
        "email": "user@example.com",
        "full_name": "Demo User",
        "hashed_password": "$2b$12$LDJ17VPlGQC3CQxSw5BbcOEzC1/r1JF4Z26M5sBYMXcYT1f9MuXvW",  # "password"
        "disabled": False
    },
    "admin@example.com": {
        "id": "admin1",
        "username": "admin@example.com",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": "$2b$12$LDJ17VPlGQC3CQxSw5BbcOEzC1/r1JF4Z26M5sBYMXcYT1f9MuXvW",  # "password"
        "disabled": False,
        "is_admin": True
    }
}

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Encode token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

def decode_token(token: str) -> Dict:
    """
    Decode a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.error(f"Failed to decode token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token from the request
        
    Returns:
        User data
        
    Raises:
        HTTPException: If token is invalid or user is not found
    """
    # For development and testing, allow a simulated user if enabled
    if os.getenv("ENABLE_DEV_USER", "").lower() == "true":
        return {
            "id": "dev_user_1",
            "username": "dev_user",
            "email": "dev@example.com",
            "full_name": "Development User"
        }
    
    # Decode token
    payload = decode_token(token)
    
    # Get user from decoded token
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from "database"
    user = DEMO_USERS.get(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is disabled
    if user.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Get the current user and verify they are an admin.
    
    Args:
        current_user: Current user data
        
    Returns:
        Admin user data
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return current_user 