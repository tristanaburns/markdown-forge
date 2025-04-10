"""
Authentication service for Markdown Forge.

This module provides authentication functionality including JWT token handling,
password hashing, and user authentication.
"""

import datetime
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from .error_handler import AuthenticationError, handle_errors
from .logger import app_logger, error_logger

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT configuration
SECRET_KEY = "your-secret-key"  # TODO: Move to config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    """Token response model."""
    
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""
    
    username: Optional[str] = None


class User(BaseModel):
    """User model."""
    
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    """User model with hashed password."""
    
    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: The plain text password
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


@handle_errors
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    
    # Encode the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Log token creation
    app_logger.info(
        "Created access token",
        extra={
            "username": data.get("sub"),
            "expires": expire.isoformat(),
        },
    )
    
    return encoded_jwt


@handle_errors
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from a JWT token.
    
    Args:
        token: The JWT token
        
    Returns:
        User: The current user
        
    Raises:
        AuthenticationError: If the token is invalid
    """
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise AuthenticationError("Could not validate credentials")
        
        token_data = TokenData(username=username)
        
        # TODO: Get user from database
        user = get_user(username=token_data.username)
        
        if user is None:
            raise AuthenticationError("User not found")
        
        return user
    
    except JWTError as e:
        error_logger.error(
            "JWT decode error",
            extra={
                "error": str(e),
            },
            exc_info=True,
        )
        raise AuthenticationError("Could not validate credentials")


@handle_errors
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The current user
        
    Returns:
        User: The current active user
        
    Raises:
        AuthenticationError: If the user is disabled
    """
    if current_user.disabled:
        raise AuthenticationError("Inactive user")
    
    return current_user


@handle_errors
def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user.
    
    Args:
        username: The username
        password: The password
        
    Returns:
        Optional[User]: The authenticated user, or None if authentication fails
    """
    # TODO: Get user from database
    user = get_user(username=username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# TODO: Replace with database implementation
def get_user(username: str) -> Optional[UserInDB]:
    """
    Get a user by username.
    
    Args:
        username: The username
        
    Returns:
        Optional[UserInDB]: The user, or None if not found
    """
    # This is a placeholder implementation
    # Replace with actual database query
    fake_users_db = {
        "johndoe": {
            "username": "johndoe",
            "full_name": "John Doe",
            "email": "johndoe@example.com",
            "hashed_password": get_password_hash("secret"),
            "disabled": False,
        }
    }
    
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    
    return None


# Export functions and classes
__all__ = [
    "Token",
    "TokenData",
    "User",
    "UserInDB",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "get_current_user",
    "get_current_active_user",
    "authenticate_user",
] 