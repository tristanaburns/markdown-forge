"""
Conversion router for Markdown Forge.
This module provides endpoints for file conversion operations.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import File, ConversionStatus
from ..services.markdown_converter import MarkdownConverter
from ..services.conversion_queue import ConversionQueue
from ..utils.error_handler import AppError
from ..utils.conversion_error_handler import ConversionError, handle_conversion_error

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/convert",
    tags=["conversion"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models for request/response
class ConversionRequest(BaseModel):
    """Model for conversion request."""
    file_id: int = Field(..., description="ID of the file to convert")
    formats: List[str] = Field(..., description="Formats to convert to")
    template_id: Optional[int] = Field(None, description="Optional template ID to use")

class ConversionResponse(BaseModel):
    """Model for conversion response."""
    file_id: int = Field(..., description="ID of the file")
    status: str = Field(..., description="Conversion status")
    converted_files: Dict[str, str] = Field(..., description="Paths to converted files")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    queue_position: Optional[int] = Field(None, description="Position in conversion queue")

class ConversionStatusResponse(BaseModel):
    """Model for conversion status response."""
    file_id: int = Field(..., description="ID of the file")
    status: str = Field(..., description="Conversion status")
    converted_files: Dict[str, str] = Field(..., description="Paths to converted files")
    error: Optional[str] = Field(None, description="Error message if conversion failed")
    progress: Optional[float] = Field(None, description="Conversion progress (0-100)")

class QueueStatusResponse(BaseModel):
    """Model for queue status response."""
    queue_length: int = Field(..., description="Number of files in queue")
    active_conversions: int = Field(..., description="Number of active conversions")
    estimated_wait_time: Optional[str] = Field(None, description="Estimated wait time")

# Initialize conversion queue
conversion_queue = ConversionQueue()

# Startup event
@router.on_event("startup")
async def startup_event():
    """Start the conversion queue on application startup."""
    logger.info("Starting conversion queue")
    await conversion_queue.start()

# Shutdown event
@router.on_event("shutdown")
async def shutdown_event():
    """Stop the conversion queue on application shutdown."""
    logger.info("Stopping conversion queue")
    await conversion_queue.stop()

@router.post("/", response_model=ConversionResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_conversion(
    request: ConversionRequest,
    db: Session = Depends(get_db)
):
    """
    Start a file conversion.
    
    Args:
        request: Conversion request
        db: Database session
        
    Returns:
        ConversionResponse: Conversion response with status and file paths
    """
    try:
        # Get file from database
        file = db.query(File).filter(File.id == request.file_id).first()
        if not file:
            raise AppError(f"File with id {request.file_id} not found", status_code=404)
            
        # Add task to conversion queue
        task_id = await conversion_queue.add_task(
            file_id=request.file_id,
            formats=request.formats,
            template_id=request.template_id
        )
        
        # Get queue status
        queue_status = await conversion_queue.get_queue_status()
        
        # Calculate estimated completion time
        estimated_completion = None
        if queue_status["active_conversions"] < queue_status["max_concurrent_tasks"]:
            estimated_completion = "5 minutes"  # Placeholder
        else:
            position = queue_status["queue_length"] - queue_status["active_conversions"]
            estimated_minutes = position * 5  # Assuming 5 minutes per conversion
            estimated_completion = f"{estimated_minutes} minutes"
            
        # Return response
        return ConversionResponse(
            file_id=request.file_id,
            status="queued",
            converted_files={},
            estimated_completion=estimated_completion,
            queue_position=position if queue_status["active_conversions"] >= queue_status["max_concurrent_tasks"] else None
        )
        
    except AppError as e:
        logger.error(f"Error starting conversion: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error starting conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversion: {str(e)}"
        )

@router.get("/{file_id}/status", response_model=ConversionStatusResponse)
async def get_conversion_status(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the conversion status for a file.
    
    Args:
        file_id: ID of the file
        db: Database session
        
    Returns:
        ConversionStatusResponse: Conversion status response
    """
    try:
        # Get file from database
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            raise AppError(f"File with id {file_id} not found", status_code=404)
            
        # Check queue status
        queue_status = await conversion_queue.get_file_status(file_id)
        
        # If file is in queue, return queue status
        if queue_status:
            return ConversionStatusResponse(
                file_id=file_id,
                status=queue_status["status"],
                converted_files={},
                error=queue_status.get("error"),
                progress=queue_status.get("progress")
            )
            
        # If file is not in queue, check database status
        if file.conversion_status == ConversionStatus.COMPLETED:
            # Parse converted files from JSON
            converted_files = {}
            if file.converted_files:
                try:
                    import json
                    converted_files = json.loads(file.converted_files)
                except Exception as e:
                    logger.error(f"Error parsing converted files: {str(e)}")
                    
            return ConversionStatusResponse(
                file_id=file_id,
                status="completed",
                converted_files=converted_files,
                error=None,
                progress=100
            )
        elif file.conversion_status == ConversionStatus.FAILED:
            return ConversionStatusResponse(
                file_id=file_id,
                status="failed",
                converted_files={},
                error=file.conversion_error,
                progress=0
            )
        else:
            return ConversionStatusResponse(
                file_id=file_id,
                status="unknown",
                converted_files={},
                error=None,
                progress=0
            )
            
    except AppError as e:
        logger.error(f"Error getting conversion status: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error getting conversion status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversion status: {str(e)}"
        )

@router.get("/{file_id}/download/{format}")
async def download_converted_file(
    file_id: int,
    format: str,
    db: Session = Depends(get_db)
):
    """
    Download a converted file.
    
    Args:
        file_id: ID of the file
        format: Format of the file to download
        db: Database session
        
    Returns:
        FileResponse: File response
    """
    try:
        # Get file from database
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            raise AppError(f"File with id {file_id} not found", status_code=404)
            
        # Check if conversion is completed
        if file.conversion_status != ConversionStatus.COMPLETED:
            raise AppError("Conversion not completed", status_code=400)
            
        # Parse converted files from JSON
        converted_files = {}
        if file.converted_files:
            try:
                import json
                converted_files = json.loads(file.converted_files)
            except Exception as e:
                logger.error(f"Error parsing converted files: {str(e)}")
                raise AppError("Error parsing converted files", status_code=500)
                
        # Check if requested format exists
        if format not in converted_files:
            raise AppError(f"Format {format} not found", status_code=404)
            
        # Return file
        file_path = converted_files[format]
        return FileResponse(
            path=file_path,
            filename=f"{file.original_name}.{format}",
            media_type=f"application/{format}"
        )
        
    except AppError as e:
        logger.error(f"Error downloading converted file: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error downloading converted file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download converted file: {str(e)}"
        )

@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """
    Get the status of the conversion queue.
    
    Returns:
        QueueStatusResponse: Queue status response
    """
    try:
        # Get queue status
        queue_status = await conversion_queue.get_queue_status()
        
        # Calculate estimated wait time
        estimated_wait_time = None
        if queue_status["queue_length"] > queue_status["active_conversions"]:
            position = queue_status["queue_length"] - queue_status["active_conversions"]
            estimated_minutes = position * 5  # Assuming 5 minutes per conversion
            estimated_wait_time = f"{estimated_minutes} minutes"
            
        # Return response
        return QueueStatusResponse(
            queue_length=queue_status["queue_length"],
            active_conversions=queue_status["active_conversions"],
            estimated_wait_time=estimated_wait_time
        )
        
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}"
        ) 