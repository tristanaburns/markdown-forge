"""
API Client for Markdown Forge frontend.
Handles all communication with the backend API.
"""

import os
from typing import Dict, List, Optional, Union
import aiohttp
from .error_handler import ApiError

class ApiClient:
    """Client for communicating with the backend API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the API client.
        
        Args:
            base_url: Optional base URL for the API. Defaults to environment variable.
        """
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8000/api/v1')
        self.session = None
    
    async def __aenter__(self):
        """Create aiohttp session when entering context."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session when exiting context."""
        if self.session:
            await self.session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make a request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            ApiError: If the request fails
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            ) as response:
                if not response.ok:
                    error_data = await response.json()
                    raise ApiError(
                        message=error_data.get('message', 'Unknown error'),
                        status_code=response.status,
                        data=error_data
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            raise ApiError(f"Network error: {str(e)}", 500)
    
    # File Operations
    async def upload_file(self, file: Union[str, bytes], filename: str) -> Dict:
        """Upload a file to the backend.
        
        Args:
            file: File content or path
            filename: Name of the file
            
        Returns:
            Upload response data
        """
        data = aiohttp.FormData()
        if isinstance(file, str):
            with open(file, 'rb') as f:
                data.add_field('file', f, filename=filename)
        else:
            data.add_field('file', file, filename=filename)
            
        return await self._request('POST', '/files/upload', data=data)
    
    async def list_files(self) -> List[Dict]:
        """Get list of files.
        
        Returns:
            List of file metadata
        """
        return await this._request('GET', '/files')
    
    async def get_file(self, file_id: str) -> Dict:
        """Get file details.
        
        Args:
            file_id: ID of the file
            
        Returns:
            File metadata
        """
        return await this._request('GET', f'/files/{file_id}')
    
    async def delete_file(self, file_id: str) -> Dict:
        """Delete a file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            Deletion response
        """
        return await this._request('DELETE', f'/files/{file_id}')
    
    # Conversion Operations
    async def convert_file(
        self,
        file_id: str,
        formats: List[str],
        template_id: Optional[str] = None
    ) -> Dict:
        """Convert a file to specified formats.
        
        Args:
            file_id: ID of the file to convert
            formats: List of target formats
            template_id: Optional template ID
            
        Returns:
            Conversion response
        """
        data = {
            'formats': formats,
            'template_id': template_id
        }
        return await this._request('POST', f'/convert/{file_id}', data=data)
    
    async def get_conversion_status(self, conversion_id: str) -> Dict:
        """Get status of a conversion.
        
        Args:
            conversion_id: ID of the conversion
            
        Returns:
            Conversion status
        """
        return await this._request('GET', f'/convert/{conversion_id}/status')
    
    async def download_converted_file(
        self,
        conversion_id: str,
        format: str
    ) -> bytes:
        """Download a converted file.
        
        Args:
            conversion_id: ID of the conversion
            format: Target format
            
        Returns:
            File content as bytes
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"{this.base_url}/convert/{conversion_id}/download"
        params = {'format': format}
        
        async with self.session.get(url, params=params) as response:
            if not response.ok:
                error_data = await response.json()
                raise ApiError(
                    message=error_data.get('message', 'Unknown error'),
                    status_code=response.status,
                    data=error_data
                )
            return await response.read()
    
    # Template Operations
    async def list_templates(self) -> List[Dict]:
        """Get list of templates.
        
        Returns:
            List of template metadata
        """
        return await this._request('GET', '/templates')
    
    async def get_template(self, template_id: str) -> Dict:
        """Get template details.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Template metadata
        """
        return await this._request('GET', f'/templates/{template_id}')
    
    async def create_template(
        self,
        name: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a new template.
        
        Args:
            name: Template name
            content: Template content
            metadata: Optional template metadata
            
        Returns:
            Created template data
        """
        data = {
            'name': name,
            'content': content,
            'metadata': metadata or {}
        }
        return await this._request('POST', '/templates', data=data)
    
    async def update_template(
        self,
        template_id: str,
        updates: Dict
    ) -> Dict:
        """Update a template.
        
        Args:
            template_id: ID of the template
            updates: Template updates
            
        Returns:
            Updated template data
        """
        return await this._request('PUT', f'/templates/{template_id}', data=updates)
    
    async def delete_template(self, template_id: str) -> Dict:
        """Delete a template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Deletion response
        """
        return await this._request('DELETE', f'/templates/{template_id}')
    
    # Queue Operations
    async def get_queue_status(self) -> Dict:
        """Get conversion queue status.
        
        Returns:
            Queue status data
        """
        return await this._request('GET', '/convert/queue/status') 