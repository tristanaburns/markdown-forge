"""
File management router for Markdown Forge.
This module handles file operation endpoints.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
from datetime import datetime
import os

from database import get_db
from models import User, File as FileModel, ConversionStatus
from auth import get_current_active_user
from services.file_manager import FileManager
from services.markdown_converter import MarkdownConverter
from utils.error_handler import AppError, register_error_handlers
from utils.rate_limiter import rate_limit

router = APIRouter(prefix="/api/v1/files", tags=["files"])

# Initialize services
file_manager = FileManager(
    upload_dir="data/uploads",
    output_dir="data/output"
)
markdown_converter = MarkdownConverter(output_dir="data/output")

class FileResponse(BaseModel):
    """Schema for file response."""
    id: int
    name: str
    original_filename: str
    file_type: str
    created_at: str
    conversion_status: str | None = None
    conversion_error: str | None = None
    converted_files: dict | None = None
    conversion_started_at: str | None = None
    conversion_completed_at: str | None = None

    class Config:
        """Pydantic config."""
        from_attributes = True

class FileRename(BaseModel):
    """Schema for file rename request."""
    new_name: str

@router.post("/upload", response_model=FileResponse)
@rate_limit(max_requests=10, window_seconds=60)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Upload a markdown file.
    
    Args:
        file (UploadFile): The file to upload
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        FileResponse: Uploaded file data
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.md', '.markdown')):
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Only markdown files are allowed"
            )
        
        # Save file
        file_entry = await file_manager.save_upload_file(file, current_user)
        db.add(file_entry)
        db.commit()
        db.refresh(file_entry)
        
        return file_entry
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/", response_model=List[FileResponse])
@rate_limit(max_requests=30, window_seconds=60)
async def list_files(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List user's files.
    
    Args:
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        List[FileResponse]: List of user's files
    """
    try:
        files = db.query(FileModel).filter(FileModel.owner_id == current_user.id).all()
        return files
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@router.get("/{file_id}", response_model=FileResponse)
@rate_limit(max_requests=30, window_seconds=60)
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get file details.
    
    Args:
        file_id (int): ID of the file
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        FileResponse: File data
    """
    try:
        file_entry = db.query(FileModel).filter(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        ).first()
        
        if not file_entry:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="File not found"
            )
        
        return file_entry
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file: {str(e)}"
        )

@router.get("/{file_id}/download")
@rate_limit(max_requests=20, window_seconds=60)
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Download a file.
    
    Args:
        file_id (int): ID of the file to download
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        Response: File download response
    """
    try:
        file_entry = db.query(FileModel).filter(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        ).first()
        
        if not file_entry:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="File not found"
            )
        
        file_path = file_entry.file_path
        if not os.path.exists(file_path):
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="File not found on disk"
            )
        
        return Response(
            content=open(file_path, "rb").read(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_entry.original_filename}"
            }
        )
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.delete("/{file_id}")
@rate_limit(max_requests=10, window_seconds=60)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a file.
    
    Args:
        file_id (int): ID of the file to delete
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        dict: Success message
    """
    try:
        file_entry = db.query(FileModel).filter(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        ).first()
        
        if not file_entry:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="File not found"
            )
        
        file_manager.delete_file(file_id, db)
        return {"message": "File deleted successfully"}
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.put("/{file_id}/rename", response_model=FileResponse)
@rate_limit(max_requests=10, window_seconds=60)
async def rename_file(
    file_id: int,
    rename_data: FileRename,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Rename a file.
    
    Args:
        file_id (int): ID of the file to rename
        rename_data (FileRename): New name for the file
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        FileResponse: Updated file data
    """
    try:
        file_entry = db.query(FileModel).filter(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        ).first()
        
        if not file_entry:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="File not found"
            )
        
        updated_file = file_manager.rename_file(file_id, rename_data.new_name, db)
        return updated_file
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rename file: {str(e)}"
        )

@router.post("/{file_id}/convert")
@rate_limit(max_requests=5, window_seconds=60)
async def convert_file(
    file_id: int,
    formats: List[str] = ["html", "pdf", "docx", "png"],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Convert a markdown file to other formats.
    
    Args:
        file_id (int): ID of the file to convert
        formats (List[str]): List of formats to convert to
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        dict: Paths to converted files
    """
    try:
        file_entry = db.query(FileModel).filter(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        ).first()
        
        if not file_entry:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="File not found"
            )
        
        # Update conversion status
        file_entry.conversion_status = ConversionStatus.IN_PROGRESS
        file_entry.conversion_started_at = datetime.utcnow()
        file_entry.conversion_error = None
        db.commit()
        
        # Read markdown content
        with open(file_entry.file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert file
        results = markdown_converter.convert(
            markdown_content,
            file_entry.name,
            formats
        )
        
        # Update conversion status
        file_entry.conversion_status = ConversionStatus.COMPLETED
        file_entry.conversion_completed_at = datetime.utcnow()
        file_entry.converted_files = json.dumps(results)
        db.commit()
        
        return results
    except AppError as e:
        # Update conversion status on error
        if file_entry:
            file_entry.conversion_status = ConversionStatus.FAILED
            file_entry.conversion_error = e.message
            file_entry.conversion_completed_at = datetime.utcnow()
            db.commit()
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        # Update conversion status on error
        if file_entry:
            file_entry.conversion_status = ConversionStatus.FAILED
            file_entry.conversion_error = str(e)
            file_entry.conversion_completed_at = datetime.utcnow()
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert file: {str(e)}"
        ) 