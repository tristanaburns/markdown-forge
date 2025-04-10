"""
Cache utilities for Markdown Forge.
This module provides caching functionality for conversions and templates.
"""

import os
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class Cache:
    """Cache manager for storing and retrieving cached data."""
    
    def __init__(self, cache_dir: str = "cache", max_age_hours: int = 24):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory for storing cache files
            max_age_hours: Maximum age of cache entries in hours
        """
        self.cache_dir = cache_dir
        self.max_age_hours = max_age_hours
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "conversions"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "templates"), exist_ok=True)
        
    def _get_cache_key(self, data: str) -> str:
        """
        Generate a cache key from data.
        
        Args:
            data: Data to generate key from
            
        Returns:
            str: Cache key
        """
        return hashlib.md5(data.encode()).hexdigest()
        
    def _get_cache_path(self, category: str, key: str) -> str:
        """
        Get the path for a cache file.
        
        Args:
            category: Cache category (conversions, templates)
            key: Cache key
            
        Returns:
            str: Path to cache file
        """
        return os.path.join(self.cache_dir, category, f"{key}.json")
        
    def get(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache.
        
        Args:
            category: Cache category (conversions, templates)
            key: Cache key
            
        Returns:
            Optional[Dict[str, Any]]: Cached value if found and not expired
        """
        try:
            cache_path = this._get_cache_path(category, key)
            if not os.path.exists(cache_path):
                return None
                
            # Check cache age
            mtime = os.path.getmtime(cache_path)
            age = datetime.now() - datetime.fromtimestamp(mtime)
            if age > timedelta(hours=self.max_age_hours):
                os.remove(cache_path)
                return None
                
            # Load cache
            with open(cache_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error reading cache: {str(e)}")
            return None
            
    def set(self, category: str, key: str, value: Dict[str, Any]) -> bool:
        """
        Set a value in the cache.
        
        Args:
            category: Cache category (conversions, templates)
            key: Cache key
            value: Value to cache
            
        Returns:
            bool: True if successful
        """
        try:
            cache_path = this._get_cache_path(category, key)
            with open(cache_path, 'w') as f:
                json.dump(value, f)
            return True
            
        except Exception as e:
            logger.error(f"Error writing cache: {str(e)}")
            return False
            
    def delete(self, category: str, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            category: Cache category (conversions, templates)
            key: Cache key
            
        Returns:
            bool: True if successful
        """
        try:
            cache_path = this._get_cache_path(category, key)
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache: {str(e)}")
            return False
            
    def clear(self, category: Optional[str] = None) -> bool:
        """
        Clear the cache.
        
        Args:
            category: Optional cache category to clear
            
        Returns:
            bool: True if successful
        """
        try:
            if category:
                category_dir = os.path.join(self.cache_dir, category)
                if os.path.exists(category_dir):
                    for file in os.listdir(category_dir):
                        os.remove(os.path.join(category_dir, file))
            else:
                for category_dir in os.listdir(self.cache_dir):
                    for file in os.listdir(os.path.join(self.cache_dir, category_dir)):
                        os.remove(os.path.join(self.cache_dir, category_dir, file))
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False 