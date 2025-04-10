import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid
from collections import deque

from models.queue import QueueItem, QueueStatus, ConversionHistoryItem
from services.conversion_service import ConversionService
from services.file_service import FileService
from utils.logger import get_logger

logger = get_logger(__name__)

class ConversionQueue:
    """
    A queue for managing document conversion tasks.
    Provides batch processing, concurrent execution, and status tracking.
    """
    
    def __init__(self, max_concurrent_tasks: int = 5, batch_size: int = 5):
        """
        Initialize the conversion queue.
        
        Args:
            max_concurrent_tasks: Maximum number of tasks to run concurrently
            batch_size: Default batch size for processing
        """
        self.queue = asyncio.Queue()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.batch_size = batch_size
        self.processing_files: Set[str] = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.history: Dict[str, ConversionHistoryItem] = {}
        
        # Performance metrics
        self.completed_count = 0
        self.failed_count = 0
        self.total_processing_time = 0
        
        # Services
        self.conversion_service = ConversionService()
        self.file_service = FileService()
        
        # Start the queue processor
        self.queue_processor_task = asyncio.create_task(self._process_queue())
        
        logger.info(f"Conversion queue initialized with max_concurrent_tasks={max_concurrent_tasks}, batch_size={batch_size}")
    
    async def add_task(self, file_id: str, input_format: str, output_format: str, 
                      user_id: str, task_id: str = None, options: Dict[str, Any] = None) -> str:
        """
        Add a conversion task to the queue.
        
        Args:
            file_id: ID of the file to convert
            input_format: Format of the input file
            output_format: Desired output format
            user_id: ID of the user requesting the conversion
            task_id: Optional task ID (generated if not provided)
            options: Optional conversion options
            
        Returns:
            Task ID of the queued conversion
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
            
        if options is None:
            options = {}
        
        # Get file information
        file_info = await self.file_service.get_file(file_id)
        if not file_info:
            raise ValueError(f"File with ID {file_id} not found")
        
        file_name = file_info.get('name', f"file_{file_id}")
        
        # Create queue item
        queue_item = QueueItem(
            id=task_id,
            file_id=file_id,
            file_name=file_name,
            input_format=input_format,
            output_format=output_format,
            user_id=user_id,
            options=options
        )
        
        # Add to queue
        await self.queue.put(queue_item)
        logger.info(f"Task {task_id} added to queue: {file_name} -> {output_format}")
        
        return task_id
    
    async def add_batch(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """
        Add a batch of tasks to the queue.
        
        Args:
            tasks: List of task dictionaries with file_id, input_format, output_format, etc.
            
        Returns:
            List of task IDs
        """
        task_ids = []
        
        for task in tasks:
            task_id = await self.add_task(
                file_id=task['file_id'],
                input_format=task.get('input_format', 'auto'),
                output_format=task['output_format'],
                user_id=task['user_id'],
                task_id=task.get('task_id'),
                options=task.get('options', {})
            )
            task_ids.append(task_id)
        
        logger.info(f"Added batch of {len(tasks)} tasks to queue")
        return task_ids
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status information or None if not found
        """
        # Check active tasks
        for item in self.active_tasks:
            if item.id == task_id:
                return {
                    "task_id": item.id,
                    "file_id": item.file_id,
                    "status": item.status,
                    "progress": item.progress,
                    "created_at": item.created_at,
                    "started_at": item.started_at,
                    "completed_at": item.completed_at,
                    "error": item.error
                }
        
        # Check history
        if task_id in self.history:
            history_item = self.history[task_id]
            return {
                "task_id": history_item.id,
                "file_id": history_item.file_id,
                "status": history_item.status,
                "created_at": history_item.timestamp,
                "completed_at": history_item.timestamp,
                "error": history_item.error
            }
        
        # Check pending queue
        queue_size = self.queue.qsize()
        pending_items = []
        
        if queue_size > 0:
            # Save queue items temporarily
            for _ in range(queue_size):
                item = await self.queue.get()
                pending_items.append(item)
                if item.id == task_id:
                    # Found the task, put all items back and return status
                    for pending_item in pending_items:
                        await self.queue.put(pending_item)
                    
                    return {
                        "task_id": item.id,
                        "file_id": item.file_id,
                        "status": item.status,
                        "progress": item.progress,
                        "created_at": item.created_at,
                        "started_at": None,
                        "completed_at": None,
                        "error": None
                    }
            
            # Put all items back if not found
            for item in pending_items:
                await self.queue.put(item)
        
        # Task not found
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task if it's still in the queue or processing.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled, False if not found or already completed
        """
        # Check if task is in active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.cancel()
            self.active_tasks.pop(task_id)
            
            # Add to history as cancelled
            self.history[task_id] = ConversionHistoryItem(
                id=task_id,
                file_id=task.file_id,
                file_name=task.file_name,
                output_format=task.output_format,
                status="Cancelled",
                timestamp=datetime.now(),
                user_id=task.user_id
            )
            
            logger.info(f"Task {task_id} cancelled")
            return True
        
        # Check pending queue
        queue_size = self.queue.qsize()
        pending_items = []
        
        if queue_size > 0:
            found = False
            # Save queue items temporarily
            for _ in range(queue_size):
                item = await self.queue.get()
                if item.id == task_id:
                    found = True
                    # Add to history as cancelled
                    self.history[task_id] = ConversionHistoryItem(
                        id=task_id,
                        file_id=item.file_id,
                        file_name=item.file_name,
                        output_format=item.output_format,
                        status="Cancelled",
                        timestamp=datetime.now(),
                        user_id=item.user_id
                    )
                    logger.info(f"Task {task_id} cancelled from queue")
                else:
                    pending_items.append(item)
            
            # Put remaining items back
            for item in pending_items:
                await self.queue.put(item)
            
            if found:
                return True
        
        # Task not found or already completed
        return False
    
    async def retry_task(self, task_id: str) -> bool:
        """
        Retry a failed conversion task.
        
        Args:
            task_id: ID of the task to retry
            
        Returns:
            True if task was requeued, False if not found or not failed
        """
        # Check if task is in history and failed
        if task_id in self.history and self.history[task_id].status == "Failed":
            history_item = self.history[task_id]
            
            # Create new queue item
            queue_item = QueueItem(
                id=task_id,
                file_id=history_item.file_id,
                file_name=history_item.file_name,
                input_format="auto",  # We may not have this info in history
                output_format=history_item.output_format,
                user_id=history_item.user_id,
                options=history_item.options,
                created_at=datetime.now()
            )
            
            # Add to queue
            await self.queue.put(queue_item)
            
            # Remove from history
            self.history.pop(task_id)
            
            logger.info(f"Task {task_id} requeued for retry")
            return True
        
        return False
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the conversion queue.
        
        Returns:
            Dictionary with queue statistics
        """
        queue_size = self.queue.qsize()
        processing_count = len(self.processing_files)
        
        # Calculate average processing time if we have completed tasks
        avg_processing_time = None
        if self.completed_count > 0:
            avg_processing_time = self.total_processing_time / self.completed_count
        
        return {
            "size": queue_size,
            "processing": processing_count,
            "completed": self.completed_count,
            "failed": self.failed_count,
            "total_processed": self.completed_count + self.failed_count,
            "avg_processing_time": avg_processing_time
        }
    
    async def get_active_conversions(self) -> List[Dict[str, Any]]:
        """
        Get information about currently active conversions.
        
        Returns:
            List of active conversion details
        """
        active_conversions = []
        
        for task_id, task in self.active_tasks.items():
            active_conversions.append({
                "id": task_id,
                "file_name": task.file_name,
                "output_format": task.output_format,
                "progress": task.progress,
                "status": "Processing"
            })
        
        return active_conversions
    
    async def get_conversion_history(self, limit: int = 50, offset: int = 0, 
                                    status: Optional[str] = None, 
                                    output_format: Optional[str] = None,
                                    user_id: Optional[str] = None) -> List[ConversionHistoryItem]:
        """
        Get conversion history, with optional filtering.
        
        Args:
            limit: Maximum number of history items to return
            offset: Number of items to skip
            status: Filter by status (e.g., "Completed", "Failed")
            output_format: Filter by output format (e.g., "pdf", "docx")
            user_id: Filter by user ID
            
        Returns:
            List of conversion history items
        """
        history_items = list(self.history.values())
        
        # Apply filters
        if status:
            history_items = [item for item in history_items if item.status.lower() == status.lower()]
        
        if output_format:
            history_items = [item for item in history_items if item.output_format.lower() == output_format.lower()]
        
        if user_id:
            history_items = [item for item in history_items if item.user_id == user_id]
        
        # Sort by timestamp (newest first)
        history_items.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        return history_items[offset:offset+limit]
    
    async def clear_conversion_history(self, user_id: Optional[str] = None) -> bool:
        """
        Clear conversion history.
        
        Args:
            user_id: If provided, only clear history for this user
            
        Returns:
            True if history was cleared
        """
        if user_id:
            # Clear only for specific user
            keys_to_remove = [
                task_id for task_id, item in self.history.items() 
                if item.user_id == user_id
            ]
            for task_id in keys_to_remove:
                self.history.pop(task_id)
                
            logger.info(f"Cleared conversion history for user {user_id}: {len(keys_to_remove)} items")
        else:
            # Clear all history
            count = len(self.history)
            self.history.clear()
            logger.info(f"Cleared all conversion history: {count} items")
        
        return True
    
    async def delete_history_item(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a specific history item.
        
        Args:
            task_id: ID of the history item to delete
            user_id: If provided, verify the item belongs to this user
            
        Returns:
            True if item was deleted, False if not found
        """
        if task_id in self.history:
            history_item = self.history[task_id]
            
            # Check if item belongs to user if user_id is provided
            if user_id and history_item.user_id != user_id:
                logger.warning(f"User {user_id} attempted to delete history item {task_id} belonging to another user")
                return False
            
            # Delete item
            self.history.pop(task_id)
            logger.info(f"Deleted history item {task_id}")
            return True
        
        return False
    
    async def _process_queue(self):
        """
        Process tasks from the queue.
        This runs continuously in the background.
        """
        while True:
            try:
                # Process tasks in batches for better efficiency
                if not self.queue.empty() and len(self.processing_files) < self.max_concurrent_tasks:
                    # Get a batch of tasks (up to batch_size or remaining capacity)
                    available_slots = self.max_concurrent_tasks - len(self.processing_files)
                    batch_size = min(self.batch_size, available_slots)
                    
                    if batch_size > 0:
                        batch = []
                        
                        # Get items from queue (up to batch_size)
                        for _ in range(min(batch_size, self.queue.qsize())):
                            item = await self.queue.get()
                            batch.append(item)
                        
                        # Process batch concurrently
                        if batch:
                            tasks = []
                            for item in batch:
                                task = asyncio.create_task(self._process_task(item))
                                self.active_tasks[item.id] = task
                                tasks.append(task)
                            
                            # Wait for all tasks to complete
                            if tasks:
                                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Sleep briefly to avoid high CPU usage
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in queue processor: {str(e)}", exc_info=True)
                await asyncio.sleep(1)  # Sleep longer on error
    
    async def _process_task(self, item: QueueItem):
        """
        Process a single conversion task.
        
        Args:
            item: Queue item to process
        """
        # Mark file as processing
        self.processing_files.add(item.file_id)
        
        # Update item status
        item.status = "Processing"
        item.started_at = datetime.now()
        item.progress = 0.1  # Start with some progress indication
        
        logger.info(f"Processing task {item.id}: {item.file_name} -> {item.output_format}")
        
        start_time = time.time()
        error = None
        success = False
        
        try:
            # Update progress
            item.progress = 0.2
            
            # Get file data
            file_data = await self.file_service.get_file_content(item.file_id)
            if not file_data:
                raise ValueError(f"Could not read file content for {item.file_id}")
            
            # Update progress
            item.progress = 0.4
            
            # Perform conversion
            result = await self.conversion_service.convert(
                file_data=file_data,
                input_format=item.input_format,
                output_format=item.output_format,
                options=item.options
            )
            
            # Update progress
            item.progress = 0.8
            
            # Save converted file
            output_file_id = await self.file_service.save_file(
                name=f"{item.file_name.rsplit('.', 1)[0]}.{item.output_format}",
                content=result,
                content_type=f"application/{item.output_format}",
                user_id=item.user_id,
                parent_file_id=item.file_id
            )
            
            # Mark as completed
            item.status = "Completed"
            item.progress = 1.0
            item.completed_at = datetime.now()
            
            # Track statistics
            self.completed_count += 1
            
            success = True
            logger.info(f"Task {item.id} completed successfully")
            
        except Exception as e:
            error = str(e)
            item.status = "Failed"
            item.error = error
            item.progress = 0
            item.completed_at = datetime.now()
            
            # Track statistics
            self.failed_count += 1
            
            logger.error(f"Task {item.id} failed: {error}", exc_info=True)
            
        finally:
            # Calculate processing time
            processing_time = time.time() - start_time
            
            if success:
                self.total_processing_time += processing_time
            
            # Add to history
            self.history[item.id] = ConversionHistoryItem(
                id=item.id,
                file_id=item.file_id,
                file_name=item.file_name,
                output_format=item.output_format,
                status=item.status,
                timestamp=item.created_at,
                duration=processing_time,
                error=item.error,
                user_id=item.user_id,
                options=item.options
            )
            
            # Remove from processing files
            self.processing_files.discard(item.file_id)
            
            # Remove from active tasks
            if item.id in self.active_tasks:
                self.active_tasks.pop(item.id)
            
            # Mark queue task as done
            self.queue.task_done()
    
    async def shutdown(self):
        """
        Shutdown the queue processor.
        Should be called when the application is shutting down.
        """
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all active tasks
        for task_id, task in list(self.active_tasks.items()):
            task.cancel()
        
        logger.info("Conversion queue shutdown complete") 