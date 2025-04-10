from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import psutil
import time
import uuid

from models.conversion import ConversionRequest, ConversionResponse, ConversionStatus
from models.queue import QueueStatus, QueueItem, ConversionHistoryItem, SystemMetrics
from services.conversion_service import ConversionService
from services.queue_service import ConversionQueue
from services.auth_service import get_current_user

router = APIRouter(prefix="/conversion", tags=["conversion"])

# Get ConversionQueue instance
conversion_queue = ConversionQueue()
conversion_service = ConversionService()

@router.post("/", response_model=ConversionResponse)
async def convert_document(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Convert a document from one format to another.
    The conversion is added to the queue and processed asynchronously.
    """
    try:
        # Generate a unique ID for this conversion task
        task_id = str(uuid.uuid4())
        
        # Add the conversion task to the queue
        await conversion_queue.add_task(
            file_id=request.file_id,
            input_format=request.input_format,
            output_format=request.output_format,
            options=request.options,
            user_id=current_user["id"],
            task_id=task_id
        )
        
        return ConversionResponse(
            task_id=task_id,
            status="pending",
            message="Conversion added to queue"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}/status", response_model=ConversionStatus)
async def get_conversion_status(
    task_id: str = Path(..., description="The ID of the conversion task"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status of a specific conversion task.
    """
    try:
        status = await conversion_queue.get_task_status(task_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/cancel")
async def cancel_conversion(
    task_id: str = Path(..., description="The ID of the conversion task to cancel"),
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a pending or in-progress conversion task.
    """
    try:
        success = await conversion_queue.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be canceled")
        
        return {"success": True, "message": "Conversion task canceled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/retry")
async def retry_conversion(
    task_id: str = Path(..., description="The ID of the conversion task to retry"),
    current_user: dict = Depends(get_current_user)
):
    """
    Retry a failed conversion task.
    """
    try:
        success = await conversion_queue.retry_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be retried")
        
        return {"success": True, "message": "Conversion task retry initiated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue/status")
async def get_queue_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current status of the conversion queue, including active conversions,
    system metrics, and recent conversion history.
    """
    try:
        # Get queue statistics
        stats = await conversion_queue.get_queue_stats()
        
        # Get active conversions
        active_conversions = await conversion_queue.get_active_conversions()
        
        # Get conversion history (most recent 20 items)
        history = await conversion_queue.get_conversion_history(limit=20)
        
        # Get system metrics
        system_metrics = {
            "cpuUsage": psutil.cpu_percent(),
            "memoryUsage": psutil.virtual_memory().percent,
            "diskUsage": psutil.disk_usage('/').percent,
            "uptime": int(time.time() - psutil.boot_time())
        }
        
        return {
            "stats": stats,
            "active_conversions": active_conversions,
            "history": history,
            "system_metrics": system_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[ConversionHistoryItem])
async def get_conversion_history(
    limit: int = Query(50, description="Maximum number of history items to return"),
    offset: int = Query(0, description="Number of items to skip"),
    status: Optional[str] = Query(None, description="Filter by status"),
    format: Optional[str] = Query(None, description="Filter by output format"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the conversion history for the current user.
    """
    try:
        history = await conversion_queue.get_conversion_history(
            limit=limit,
            offset=offset,
            status=status,
            output_format=format,
            user_id=current_user["id"]
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/history/clear")
async def clear_conversion_history(
    current_user: dict = Depends(get_current_user)
):
    """
    Clear the conversion history for the current user.
    """
    try:
        success = await conversion_queue.clear_conversion_history(user_id=current_user["id"])
        return {"success": success, "message": "Conversion history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{task_id}")
async def delete_history_item(
    task_id: str = Path(..., description="The ID of the history item to delete"),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific item from the conversion history.
    """
    try:
        success = await conversion_queue.delete_history_item(task_id=task_id, user_id=current_user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="History item not found")
        
        return {"success": True, "message": "History item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=List[ConversionResponse])
async def batch_convert_documents(
    requests: List[ConversionRequest],
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Add multiple conversion tasks to the queue at once.
    """
    try:
        responses = []
        
        # Add all tasks to a batch
        batch_tasks = []
        for request in requests:
            task_id = str(uuid.uuid4())
            batch_tasks.append({
                "file_id": request.file_id,
                "input_format": request.input_format,
                "output_format": request.output_format,
                "options": request.options,
                "user_id": current_user["id"],
                "task_id": task_id
            })
            
            responses.append(ConversionResponse(
                task_id=task_id,
                status="pending",
                message="Conversion added to queue"
            ))
        
        # Add the batch to the queue
        await conversion_queue.add_batch(batch_tasks)
        
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 