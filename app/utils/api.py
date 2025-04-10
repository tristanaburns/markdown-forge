"""
API utility for handling HTTP requests to the backend.
"""

import aiohttp
import asyncio
from typing import Any, Dict, List, Optional, Union
from .config import config
from .logger import logger
import os

class ApiClient:
    """API client for making HTTP requests to the backend."""
    
    def __init__(self, base_url: str = config.api.base_url):
        """Initialize API client.
        
        Args:
            base_url: Backend API base URL
        """
        this.base_url = base_url.rstrip('/')
        this.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> 'ApiClient':
        """Create aiohttp session when entering context."""
        this.session = aiohttp.ClientSession()
        return this
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close aiohttp session when exiting context."""
        if this.session:
            await this.session.close()
            this.session = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to backend API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for aiohttp.ClientSession.request
            
        Returns:
            API response as dictionary
            
        Raises:
            aiohttp.ClientError: If request fails
            ValueError: If response is not valid JSON
        """
        if not this.session:
            raise RuntimeError("API client not initialized. Use async with context.")
        
        url = f"{this.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"Making {method} request to {url}")
        
        try:
            async with this.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments for request
            
        Returns:
            API response
        """
        return await this._request('GET', endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make POST request.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments for request
            
        Returns:
            API response
        """
        return await this._request('POST', endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments for request
            
        Returns:
            API response
        """
        return await this._request('PUT', endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments for request
            
        Returns:
            API response
        """
        return await this._request('DELETE', endpoint, **kwargs)
    
    async def upload_file(
        self,
        endpoint: str,
        file_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Upload file to backend.
        
        Args:
            endpoint: API endpoint
            file_path: Path to file to upload
            **kwargs: Additional arguments for request
            
        Returns:
            API response
        """
        if not this.session:
            raise RuntimeError("API client not initialized. Use async with context.")
        
        url = f"{this.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"Uploading file {file_path} to {url}")
        
        try:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field(
                    'file',
                    f,
                    filename=os.path.basename(file_path)
                )
                
                async with this.session.post(url, data=data, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
        except (IOError, aiohttp.ClientError) as e:
            logger.error(f"File upload failed: {str(e)}")
            raise
    
    async def download_file(
        self,
        endpoint: str,
        save_path: str,
        **kwargs
    ) -> None:
        """Download file from backend.
        
        Args:
            endpoint: API endpoint
            save_path: Path to save downloaded file
            **kwargs: Additional arguments for request
            
        Raises:
            aiohttp.ClientError: If download fails
            IOError: If file cannot be saved
        """
        if not this.session:
            raise RuntimeError("API client not initialized. Use async with context.")
        
        url = f"{this.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"Downloading file from {url} to {save_path}")
        
        try:
            async with this.session.get(url, **kwargs) as response:
                response.raise_for_status()
                
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
        except (aiohttp.ClientError, IOError) as e:
            logger.error(f"File download failed: {str(e)}")
            raise

# Create default API client instance
api = ApiClient() 