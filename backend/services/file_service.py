import asyncio
import os
import json
import uuid
from typing import Dict, List, Optional, Any, BinaryIO
from datetime import datetime
import aiofiles
import aiofiles.os
from utils.logger import get_logger

logger = get_logger(__name__)

class FileService:
    """
    Service for managing files in the application.
    Handles file storage, retrieval, metadata, and operations.
    """
    
    def __init__(self, storage_dir: str = "storage"):
        """
        Initialize the file service.
        
        Args:
            storage_dir: Directory to store files in
        """
        self.storage_dir = storage_dir
        self.files_dir = os.path.join(storage_dir, "files")
        self.metadata_dir = os.path.join(storage_dir, "metadata")
        
        # Create directories if they don't exist
        os.makedirs(self.files_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # In-memory cache of file metadata
        self.file_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"FileService initialized with storage_dir={storage_dir}")
    
    async def save_file(self, name: str, content: bytes, content_type: str, 
                      user_id: str, parent_file_id: Optional[str] = None) -> str:
        """
        Save a file to storage.
        
        Args:
            name: Name of the file
            content: File content as bytes
            content_type: MIME type of the file
            user_id: ID of the user who owns the file
            parent_file_id: ID of the parent file (for conversions)
            
        Returns:
            ID of the saved file
        """
        # Generate a unique ID for the file
        file_id = str(uuid.uuid4())
        
        # Create file path
        file_path = os.path.join(self.files_dir, file_id)
        
        # Create metadata
        metadata = {
            "id": file_id,
            "name": name,
            "content_type": content_type,
            "size": len(content),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "user_id": user_id,
            "parent_file_id": parent_file_id
        }
        
        # Save file content
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # Save metadata
        metadata_path = os.path.join(self.metadata_dir, f"{file_id}.json")
        async with aiofiles.open(metadata_path, "w") as f:
            await f.write(json.dumps(metadata, indent=2))
        
        # Update cache
        self.file_cache[file_id] = metadata
        
        logger.info(f"File saved: id={file_id}, name={name}, size={len(content)} bytes")
        return file_id
    
    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata.
        
        Args:
            file_id: ID of the file
            
        Returns:
            File metadata or None if not found
        """
        # Check cache first
        if file_id in self.file_cache:
            return self.file_cache[file_id]
        
        # Check if metadata file exists
        metadata_path = os.path.join(self.metadata_dir, f"{file_id}.json")
        if not os.path.exists(metadata_path):
            return None
        
        # Load metadata
        try:
            async with aiofiles.open(metadata_path, "r") as f:
                metadata = json.loads(await f.read())
            
            # Update cache
            self.file_cache[file_id] = metadata
            
            return metadata
        except Exception as e:
            logger.error(f"Error reading file metadata: {str(e)}", exc_info=True)
            return None
    
    async def get_file_content(self, file_id: str) -> Optional[bytes]:
        """
        Get file content.
        
        Args:
            file_id: ID of the file
            
        Returns:
            File content as bytes or None if not found
        """
        # Check if file exists
        file_path = os.path.join(self.files_dir, file_id)
        if not os.path.exists(file_path):
            return None
        
        # Read file content
        try:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            
            return content
        except Exception as e:
            logger.error(f"Error reading file content: {str(e)}", exc_info=True)
            return None
    
    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_id: ID of the file
            user_id: ID of the user who owns the file
            
        Returns:
            True if file was deleted, False if not found or not owned by user
        """
        # Get file metadata
        metadata = await self.get_file(file_id)
        if not metadata:
            return False
        
        # Check if file is owned by user
        if metadata["user_id"] != user_id:
            logger.warning(f"User {user_id} attempted to delete file {file_id} owned by {metadata['user_id']}")
            return False
        
        # Delete file content
        file_path = os.path.join(self.files_dir, file_id)
        if os.path.exists(file_path):
            try:
                await aiofiles.os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting file content: {str(e)}", exc_info=True)
                return False
        
        # Delete metadata
        metadata_path = os.path.join(self.metadata_dir, f"{file_id}.json")
        if os.path.exists(metadata_path):
            try:
                await aiofiles.os.remove(metadata_path)
            except Exception as e:
                logger.error(f"Error deleting file metadata: {str(e)}", exc_info=True)
                return False
        
        # Remove from cache
        if file_id in self.file_cache:
            del self.file_cache[file_id]
        
        logger.info(f"File deleted: id={file_id}, name={metadata['name']}")
        return True
    
    async def list_files(self, user_id: str, 
                        parent_folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files for a user.
        
        Args:
            user_id: ID of the user
            parent_folder_id: Optional parent folder ID to filter by
            
        Returns:
            List of file metadata
        """
        files = []
        
        # For this stub implementation, just scan the metadata directory
        for filename in os.listdir(self.metadata_dir):
            if not filename.endswith(".json"):
                continue
            
            file_id = filename[:-5]  # Remove .json extension
            
            metadata = await self.get_file(file_id)
            if not metadata:
                continue
            
            # Filter by user ID
            if metadata["user_id"] != user_id:
                continue
            
            # Filter by parent folder ID if specified
            if parent_folder_id is not None:
                parent = metadata.get("parent_folder_id")
                if parent != parent_folder_id:
                    continue
            
            files.append(metadata)
        
        return files
    
    async def search_files(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Search for files by name.
        
        Args:
            user_id: ID of the user
            query: Search query
            
        Returns:
            List of file metadata matching the query
        """
        files = await self.list_files(user_id)
        
        # Filter by query
        query = query.lower()
        return [file for file in files if query in file["name"].lower()]
    
    async def update_file_metadata(self, file_id: str, user_id: str, 
                                 updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update file metadata.
        
        Args:
            file_id: ID of the file
            user_id: ID of the user who owns the file
            updates: Dictionary of metadata updates
            
        Returns:
            Updated file metadata or None if not found or not owned by user
        """
        # Get file metadata
        metadata = await self.get_file(file_id)
        if not metadata:
            return None
        
        # Check if file is owned by user
        if metadata["user_id"] != user_id:
            logger.warning(f"User {user_id} attempted to update file {file_id} owned by {metadata['user_id']}")
            return None
        
        # Update metadata
        allowed_fields = ["name", "description", "tags"]
        for field in allowed_fields:
            if field in updates:
                metadata[field] = updates[field]
        
        metadata["updated_at"] = datetime.now().isoformat()
        
        # Save updated metadata
        metadata_path = os.path.join(self.metadata_dir, f"{file_id}.json")
        async with aiofiles.open(metadata_path, "w") as f:
            await f.write(json.dumps(metadata, indent=2))
        
        # Update cache
        self.file_cache[file_id] = metadata
        
        logger.info(f"File metadata updated: id={file_id}, name={metadata['name']}")
        return metadata 