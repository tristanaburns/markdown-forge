"""
Application configuration management using Pydantic.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import EmailStr, PostgresDsn, validator

class Settings(BaseSettings):
    """
    Application settings.
    
    Attributes:
        PROJECT_NAME: Name of the project
        VERSION: Version of the application
        API_V1_STR: API version prefix
        SECRET_KEY: Secret key for JWT token generation
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time in minutes
        POSTGRES_SERVER: PostgreSQL server host
        POSTGRES_USER: PostgreSQL user
        POSTGRES_PASSWORD: PostgreSQL password
        POSTGRES_DB: PostgreSQL database name
        DATABASE_URL: Complete database URL
        SMTP_TLS: Enable TLS for SMTP
        SMTP_PORT: SMTP port
        SMTP_HOST: SMTP host
        SMTP_USER: SMTP user
        SMTP_PASSWORD: SMTP password
        EMAILS_FROM_EMAIL: Default sender email
        EMAILS_FROM_NAME: Default sender name
    """
    
    PROJECT_NAME: str = "Markdown Forge"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        """Construct database URL from components."""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create global settings instance
settings = Settings() 