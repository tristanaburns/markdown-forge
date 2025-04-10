"""
Conversion queue service for Markdown Forge.
This module provides a queue-based system for managing file conversions.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import File, ConversionTemplate
from ..utils.conversion_error_handler import (
    ConversionError,
    ConversionErrorType,
    RecoveryStrategy,
    handle_conversion_error,
    is_recoverable_error,
    get_error_recovery_strategy,
    apply_recovery_strategy
)
from .markdown_converter import MarkdownConverter

# Configure logging
logger = logging.getLogger(__name__)

class ConversionQueue:
    """Service for managing a queue of file conversion tasks."""
    
    def __init__(self, db: Session, max_concurrent_tasks: int = 3):
        """
        Initialize the conversion queue service.
        
        Args:
            db: Database session
            max_concurrent_tasks: Maximum number of concurrent conversion tasks
        """
        self.db = db
        self.max_concurrent_tasks = max_concurrent_tasks
        self.queue = asyncio.Queue()
        self.processing = False
        self.active_tasks: Dict[int, asyncio.Task] = {}
        self.converter = MarkdownConverter(output_dir="converted_files")
        
    async def start(self):
        """Start the queue processor."""
        if not self.processing:
            self.processing = True
            asyncio.create_task(self._process_queue())
            logger.info("Conversion queue processor started")
            
    async def stop(self):
        """Stop the queue processor."""
        if self.processing:
            self.processing = False
            # Wait for active tasks to complete
            for task in self.active_tasks.values():
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
            logger.info("Conversion queue processor stopped")
            
    async def add_task(self, file_id: int, formats: List[str], template_id: Optional[int] = None) -> bool:
        """
        Add a file conversion task to the queue.
        
        Args:
            file_id: ID of the file to convert
            formats: List of output formats
            template_id: Optional template ID to use for conversion
            
        Returns:
            bool: True if the task was added, False if the file is already being processed
        """
        # Check if file exists and is not already being processed
        file = self.db.query(File).filter(File.id == file_id).first()
        if not file:
            logger.error(f"File not found: {file_id}")
            return False
            
        if file.id in self.active_tasks:
            logger.warning(f"File {file_id} is already being processed")
            return False
            
        # Update file status to pending
        file.conversion_status = "pending"
        file.conversion_started_at = datetime.utcnow()
        self.db.commit()
        
        # Add task to queue
        await self.queue.put({
            "file_id": file_id,
            "formats": formats,
            "template_id": template_id,
            "retry_count": 0,
            "last_error": None
        })
        
        logger.info(f"Added conversion task for file {file_id}")
        return True
        
    async def _process_queue(self):
        """Process the conversion queue."""
        while self.processing:
            # Check if we can process more tasks
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                await asyncio.sleep(1)
                continue
                
            try:
                # Get next task from queue
                task = await self.queue.get()
                file_id = task["file_id"]
                
                # Create task for file conversion
                self.active_tasks[file_id] = asyncio.create_task(
                    self._convert_file(
                        file_id,
                        task["formats"],
                        task["template_id"],
                        task["retry_count"],
                        task["last_error"]
                    )
                )
                
                # Remove task from queue
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing queue: {str(e)}")
                await asyncio.sleep(1)
                
    async def _convert_file(
        self,
        file_id: int,
        formats: List[str],
        template_id: Optional[int],
        retry_count: int,
        last_error: Optional[ConversionError]
    ):
        """
        Convert a file with error recovery.
        
        Args:
            file_id: ID of the file to convert
            formats: List of output formats
            template_id: Optional template ID to use for conversion
            retry_count: Current retry attempt count
            last_error: Previous error if this is a retry attempt
        """
        try:
            # Get file from database
            file = self.db.query(File).filter(File.id == file_id).first()
            if not file:
                logger.error(f"File not found: {file_id}")
                return
                
            # Update file status to processing
            file.conversion_status = "processing"
            self.db.commit()
            
            # Convert file
            output_files = self.converter.convert(file.file_path, formats, template_id)
            
            # Update file status to completed
            file.conversion_status = "completed"
            file.conversion_completed_at = datetime.utcnow()
            file.converted_files = output_files
            self.db.commit()
            
            logger.info(f"Successfully converted file {file_id}")
            
        except Exception as e:
            # Handle the error
            error_response = handle_conversion_error(e)
            error = ConversionError(
                message=error_response["message"],
                error_type=ConversionErrorType(error_response["code"]),
                details=error_response["details"],
                status_code=error_response["status_code"],
                recovery_attempts=retry_count,
                recovery_strategy=get_error_recovery_strategy(e)
            )
            
            # Check if error is recoverable
            if is_recoverable_error(e) and retry_count < 3:
                # Get recovery strategy
                strategy = get_error_recovery_strategy(e)
                if strategy:
                    logger.info(f"Retrying conversion with strategy: {strategy.value} (attempt {retry_count + 1}/3)")
                    
                    # Apply recovery strategy
                    result, new_error = apply_recovery_strategy(
                        strategy,
                        self._convert_file,
                        file_id,
                        formats,
                        template_id,
                        retry_count + 1,
                        error
                    )
                    
                    if new_error:
                        # If we got a new error, check if it's recoverable
                        if is_recoverable_error(new_error) and retry_count + 1 < 3:
                            # Try a different strategy
                            alternative_strategy = self._get_alternative_strategy(strategy)
                            if alternative_strategy:
                                logger.info(f"Trying alternative strategy: {alternative_strategy.value}")
                                return await self._convert_file(
                                    file_id,
                                    formats,
                                    template_id,
                                    retry_count + 1,
                                    new_error
                                )
                        
                        # If we can't recover, update file status to failed
                        file.conversion_status = "failed"
                        file.conversion_error = str(new_error)
                        self.db.commit()
                        logger.error(f"Failed to convert file {file_id} after recovery attempt: {str(new_error)}")
                        return
                    
                    return result
                    
            # If error is not recoverable or we've exhausted retries, update file status to failed
            file.conversion_status = "failed"
            file.conversion_error = str(error)
            self.db.commit()
            logger.error(f"Failed to convert file {file_id}: {str(error)}")
            
        finally:
            # Remove task from active tasks
            self.active_tasks.pop(file_id, None)
            
    def _get_alternative_strategy(self, current_strategy: RecoveryStrategy) -> Optional[RecoveryStrategy]:
        """
        Get an alternative recovery strategy if the current one fails.
        
        Args:
            current_strategy: The current recovery strategy
            
        Returns:
            Optional[RecoveryStrategy]: An alternative strategy, or None if none available
        """
        # Map of strategies to alternatives
        alternatives = {
            RecoveryStrategy.RETRY_WITH_TIMEOUT_INCREASE: RecoveryStrategy.RETRY_WITH_SIMPLIFIED_OPTIONS,
            RecoveryStrategy.RETRY_WITH_SIMPLIFIED_OPTIONS: RecoveryStrategy.RETRY_WITH_MEMORY_OPTIMIZATION,
            RecoveryStrategy.RETRY_WITH_MEMORY_OPTIMIZATION: RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.RETRY_WITH_NETWORK_RETRY: RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.RETRY_WITH_BACKOFF: RecoveryStrategy.FALLBACK_TO_ALTERNATIVE_CONVERTER
        }
        
        return alternatives.get(current_strategy)
        
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current status of the conversion queue.
        
        Returns:
            Dict[str, Any]: Dictionary containing queue status information
        """
        return {
            "queue_size": self.queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "is_processing": self.processing
        }
        
    def get_file_status(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific file conversion.
        
        Args:
            file_id: ID of the file to check
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing file status information, or None if file not found
        """
        file = self.db.query(File).filter(File.id == file_id).first()
        if not file:
            return None
            
        status = {
            "file_id": file.id,
            "status": file.conversion_status,
            "started_at": file.conversion_started_at,
            "completed_at": file.conversion_completed_at,
            "error": file.conversion_error
        }
        
        # Add queue-specific information if file is being processed
        if file.id in self.active_tasks:
            task = self.active_tasks[file.id]
            status["task"] = {
                "done": task.done(),
                "cancelled": task.cancelled(),
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
            
        return status 