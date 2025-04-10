"""
File manager service for Markdown Forge.
Handles file operations like saving, reading, and listing files.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileManager:
    """Handles file operations for Markdown Forge."""
    
    def __init__(self, upload_dir: str, metadata_file: str):
        """
        Initialize the file manager.
        
        Args:
            upload_dir (str): Directory for uploaded files
            metadata_file (str): Path to metadata JSON file
        """
        self.upload_dir = Path(upload_dir)
        self.metadata_file = Path(metadata_file)
        self.metadata: Dict = {}
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load metadata from JSON file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                logger.info("Loaded metadata successfully")
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            self.metadata = {}
    
    def _save_metadata(self) -> None:
        """Save metadata to JSON file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info("Saved metadata successfully")
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            raise
    
    def save_file(self, content: str, filename: str) -> str:
        """
        Save a Markdown file and return its ID.
        
        Args:
            content (str): File content
            filename (str): Original filename
        
        Returns:
            str: File ID
        """
        try:
            # Generate unique ID
            file_id = str(uuid.uuid4())
            
            # Save file content
            file_path = self.upload_dir / f"{file_id}.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update metadata
            self.metadata[file_id] = {
                'filename': filename,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'size': len(content),
                'formats': []
            }
            self._save_metadata()
            
            logger.info(f"Saved file {filename} with ID {file_id}")
            return file_id
        
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise
    
    def get_file_content(self, file_id: str) -> str:
        """
        Get the content of a file.
        
        Args:
            file_id (str): File ID
        
        Returns:
            str: File content
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            file_path = self.upload_dir / f"{file_id}.md"
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_id}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
        
        except Exception as e:
            logger.error(f"Error reading file {file_id}: {str(e)}")
            raise
    
    def list_files(self) -> List[Dict]:
        """
        List all files with their metadata.
        
        Returns:
            List[Dict]: List of file metadata
        """
        try:
            files = []
            for file_id, metadata in self.metadata.items():
                file_info = {
                    'id': file_id,
                    **metadata
                }
                files.append(file_info)
            
            # Sort by creation date, newest first
            files.sort(key=lambda x: x['created_at'], reverse=True)
            return files
        
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise
    
    def update_formats(self, file_id: str, formats: List[str]) -> None:
        """
        Update the list of available formats for a file.
        
        Args:
            file_id (str): File ID
            formats (List[str]): List of available formats
        """
        try:
            if file_id not in self.metadata:
                raise KeyError(f"File not found: {file_id}")
            
            self.metadata[file_id]['formats'] = formats
            self.metadata[file_id]['updated_at'] = datetime.now().isoformat()
            self._save_metadata()
            
            logger.info(f"Updated formats for {file_id}: {formats}")
        
        except Exception as e:
            logger.error(f"Error updating formats: {str(e)}")
            raise
    
    def delete_file(self, file_id: str) -> None:
        """
        Delete a file and its metadata.
        
        Args:
            file_id (str): File ID
        """
        try:
            # Delete file
            file_path = self.upload_dir / f"{file_id}.md"
            if file_path.exists():
                file_path.unlink()
            
            # Remove metadata
            if file_id in self.metadata:
                del self.metadata[file_id]
                self._save_metadata()
            
            logger.info(f"Deleted file {file_id}")
        
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise 