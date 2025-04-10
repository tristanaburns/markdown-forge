"""
File management service for Markdown Forge.
This module handles file operations including upload, download, and management.
"""

import os
import shutil
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
import logging

from models import File, User, Project

# Configure logging
logger = logging.getLogger(__name__)

class FileManager:
    """Service for managing files in the system."""

    def __init__(self, upload_dir: str, output_dir: str):
        """
        Initialize the file manager with directories.
        
        Args:
            upload_dir (str): Directory for uploaded files
            output_dir (str): Directory for converted files
        """
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        
        # Ensure directories exist
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

    async def save_upload_file(
        self,
        upload_file: UploadFile,
        user: User,
        project: Optional[Project] = None
    ) -> File:
        """
        Save an uploaded file and create database entry.
        
        Args:
            upload_file (UploadFile): The uploaded file
            user (User): The user who uploaded the file
            project (Project, optional): The project the file belongs to
            
        Returns:
            File: The created file database entry
        """
        try:
            # Generate safe filename
            filename = self._generate_safe_filename(upload_file.filename)
            file_path = os.path.join(self.upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            
            # Create database entry
            file_entry = File(
                name=filename,
                original_filename=upload_file.filename,
                file_path=file_path,
                file_type=self._get_file_type(upload_file.filename),
                owner_id=user.id,
                project_id=project.id if project else None
            )
            
            return file_entry
            
        except Exception as e:
            logger.error(f"Failed to save upload file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save upload file: {str(e)}"
            )

    def get_file_path(self, file_id: int, db: Session) -> str:
        """
        Get the file path for a given file ID.
        
        Args:
            file_id (int): The ID of the file
            db (Session): Database session
            
        Returns:
            str: Path to the file
        """
        file_entry = db.query(File).filter(File.id == file_id).first()
        if not file_entry:
            raise HTTPException(status_code=404, detail="File not found")
        return file_entry.file_path

    def delete_file(self, file_id: int, db: Session) -> None:
        """
        Delete a file and its database entry.
        
        Args:
            file_id (int): The ID of the file to delete
            db (Session): Database session
        """
        try:
            file_entry = db.query(File).filter(File.id == file_id).first()
            if not file_entry:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Delete physical file
            if os.path.exists(file_entry.file_path):
                os.remove(file_entry.file_path)
            
            # Delete database entry
            db.delete(file_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete file: {str(e)}"
            )

    def rename_file(self, file_id: int, new_name: str, db: Session) -> File:
        """
        Rename a file and update its database entry.
        
        Args:
            file_id (int): The ID of the file to rename
            new_name (str): The new name for the file
            db (Session): Database session
            
        Returns:
            File: The updated file database entry
        """
        try:
            file_entry = db.query(File).filter(File.id == file_id).first()
            if not file_entry:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Generate safe new filename
            safe_new_name = self._generate_safe_filename(new_name)
            new_path = os.path.join(self.upload_dir, safe_new_name)
            
            # Rename physical file
            if os.path.exists(file_entry.file_path):
                os.rename(file_entry.file_path, new_path)
            
            # Update database entry
            file_entry.name = safe_new_name
            file_entry.file_path = new_path
            db.commit()
            
            return file_entry
            
        except Exception as e:
            logger.error(f"Failed to rename file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to rename file: {str(e)}"
            )

    def cleanup_old_files(self, db: Session, days: int = 30) -> None:
        """
        Clean up files older than specified days.
        
        Args:
            db (Session): Database session
            days (int): Number of days after which to delete files
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get old files
            old_files = db.query(File).filter(File.created_at < cutoff_date).all()
            
            for file_entry in old_files:
                # Delete physical file
                if os.path.exists(file_entry.file_path):
                    os.remove(file_entry.file_path)
                
                # Delete database entry
                db.delete(file_entry)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cleanup old files: {str(e)}"
            )

    def _generate_safe_filename(self, filename: str) -> str:
        """
        Generate a safe filename by removing special characters.
        
        Args:
            filename (str): Original filename
            
        Returns:
            str: Safe filename
        """
        # Remove special characters and spaces
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
        return safe_name

    def _get_file_type(self, filename: str) -> str:
        """
        Get file type from filename.
        
        Args:
            filename (str): Filename
            
        Returns:
            str: File type (md, pdf, docx, html, png)
        """
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            '.md': 'md',
            '.markdown': 'md',
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.html': 'html',
            '.htm': 'html',
            '.png': 'png'
        }
        return type_map.get(ext, 'unknown') 