"""
Configuration utility for managing application settings.
"""

import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class ApiConfig:
    """API configuration settings."""
    base_url: str = "http://localhost:8000"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1

@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/app.log"
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class FileConfig:
    """File handling configuration settings."""
    upload_dir: str = "uploads"
    temp_dir: str = "temp"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list[str] = field(default_factory=lambda: [
        "md", "txt", "html", "pdf", "docx"
    ])

@dataclass
class ConversionConfig:
    """Conversion configuration settings."""
    batch_size: int = 5
    concurrent_limit: int = 3
    timeout: int = 300
    output_dir: str = "converted"

@dataclass
class Config:
    """Main configuration class."""
    debug: bool = False
    api: ApiConfig = field(default_factory=ApiConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    file: FileConfig = field(default_factory=FileConfig)
    conversion: ConversionConfig = field(default_factory=ConversionConfig)
    
    def __post_init__(self):
        """Initialize configuration after creation."""
        # Create required directories
        os.makedirs(self.logging.file.rsplit('/', 1)[0], exist_ok=True)
        os.makedirs(self.file.upload_dir, exist_ok=True)
        os.makedirs(self.file.temp_dir, exist_ok=True)
        os.makedirs(self.conversion.output_dir, exist_ok=True)
        
        # Set debug mode
        if self.debug:
            self.logging.level = "DEBUG"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create configuration from dictionary.
        
        Args:
            data: Configuration data dictionary
            
        Returns:
            Config instance
        """
        config = cls()
        
        # Update main config
        if 'debug' in data:
            config.debug = data['debug']
        
        # Update API config
        if 'api' in data:
            api_data = data['api']
            config.api = ApiConfig(
                base_url=api_data.get('base_url', config.api.base_url),
                timeout=api_data.get('timeout', config.api.timeout),
                retry_attempts=api_data.get('retry_attempts', config.api.retry_attempts),
                retry_delay=api_data.get('retry_delay', config.api.retry_delay)
            )
        
        # Update logging config
        if 'logging' in data:
            log_data = data['logging']
            config.logging = LoggingConfig(
                level=log_data.get('level', config.logging.level),
                format=log_data.get('format', config.logging.format),
                file=log_data.get('file', config.logging.file),
                max_size=log_data.get('max_size', config.logging.max_size),
                backup_count=log_data.get('backup_count', config.logging.backup_count)
            )
        
        # Update file config
        if 'file' in data:
            file_data = data['file']
            config.file = FileConfig(
                upload_dir=file_data.get('upload_dir', config.file.upload_dir),
                temp_dir=file_data.get('temp_dir', config.file.temp_dir),
                max_file_size=file_data.get('max_file_size', config.file.max_file_size),
                allowed_extensions=file_data.get(
                    'allowed_extensions',
                    config.file.allowed_extensions
                )
            )
        
        # Update conversion config
        if 'conversion' in data:
            conv_data = data['conversion']
            config.conversion = ConversionConfig(
                batch_size=conv_data.get('batch_size', config.conversion.batch_size),
                concurrent_limit=conv_data.get(
                    'concurrent_limit',
                    config.conversion.concurrent_limit
                ),
                timeout=conv_data.get('timeout', config.conversion.timeout),
                output_dir=conv_data.get('output_dir', config.conversion.output_dir)
            )
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            'debug': self.debug,
            'api': {
                'base_url': self.api.base_url,
                'timeout': self.api.timeout,
                'retry_attempts': self.api.retry_attempts,
                'retry_delay': self.api.retry_delay
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file': self.logging.file,
                'max_size': self.logging.max_size,
                'backup_count': self.logging.backup_count
            },
            'file': {
                'upload_dir': self.file.upload_dir,
                'temp_dir': self.file.temp_dir,
                'max_file_size': self.file.max_file_size,
                'allowed_extensions': self.file.allowed_extensions
            },
            'conversion': {
                'batch_size': self.conversion.batch_size,
                'concurrent_limit': self.conversion.concurrent_limit,
                'timeout': self.conversion.timeout,
                'output_dir': self.conversion.output_dir
            }
        }

# Create default configuration instance
config = Config() 