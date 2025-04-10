"""
Configuration service for Markdown Forge.
Manages application settings and environment variables.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Manages application configuration."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        
        # Default configuration
        self.defaults = {
            'upload_dir': 'data/uploads',
            'output_dir': 'data/converted',
            'metadata_file': 'data/metadata.json',
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'allowed_extensions': ['.md', '.markdown', '.mdown'],
            'pandoc_path': 'pandoc',
            'default_formats': ['html', 'pdf', 'docx', 'png'],
            'debug': False,
            'host': '0.0.0.0',
            'port': 8000,
            'secret_key': os.urandom(24).hex()
        }
        
        # Load configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file or create with defaults."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info("Loaded configuration from file")
            else:
                self.config = self.defaults.copy()
                self._save_config()
                logger.info("Created default configuration")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self.config = self.defaults.copy()
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Saved configuration to file")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key (str): Configuration key
            default (Any): Default value if key not found
        
        Returns:
            Any: Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key (str): Configuration key
            value (Any): Configuration value
        """
        try:
            self.config[key] = value
            self._save_config()
            logger.info(f"Updated configuration: {key}")
        except Exception as e:
            logger.error(f"Error setting configuration {key}: {str(e)}")
            raise
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple configuration values.
        
        Args:
            updates (Dict[str, Any]): Dictionary of updates
        """
        try:
            self.config.update(updates)
            self._save_config()
            logger.info("Updated multiple configuration values")
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            raise
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        try:
            self.config = self.defaults.copy()
            self._save_config()
            logger.info("Reset configuration to defaults")
        except Exception as e:
            logger.error(f"Error resetting configuration: {str(e)}")
            raise
    
    def validate(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Check required directories
            for dir_path in [self.get('upload_dir'), self.get('output_dir')]:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            
            # Check Pandoc installation
            pandoc_path = self.get('pandoc_path')
            if not os.path.exists(pandoc_path):
                logger.warning(f"Pandoc not found at {pandoc_path}")
                return False
            
            # Validate file size limit
            max_size = self.get('max_file_size')
            if not isinstance(max_size, int) or max_size <= 0:
                logger.error("Invalid max_file_size")
                return False
            
            # Validate allowed extensions
            extensions = self.get('allowed_extensions')
            if not isinstance(extensions, list) or not all(isinstance(ext, str) for ext in extensions):
                logger.error("Invalid allowed_extensions")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating configuration: {str(e)}")
            return False 