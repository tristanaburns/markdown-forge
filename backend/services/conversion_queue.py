"""
Conversion queue service for Markdown Forge.
This module provides a queue-based system for managing file conversions.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from sqlalchemy.orm import Session
import os
import psutil

from ..models import File, ConversionTemplate, ConversionHistory
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
    
    def __init__(this, db: Session, max_concurrent_tasks: int = 3, batch_size: int = 5):
        """
        Initialize the conversion queue service.
        
        Args:
            db: Database session
            max_concurrent_tasks: Maximum number of concurrent conversion tasks
            batch_size: Maximum number of tasks to process in a batch
        """
        this.db = db
        this.max_concurrent_tasks = max_concurrent_tasks
        this.batch_size = batch_size
        this.queue = asyncio.Queue()
        this.processing = False
        this.active_tasks: Dict[int, asyncio.Task] = {}
        this.processing_files: Set[int] = set()
        this.converter = MarkdownConverter(output_dir="converted_files")
        
    async def start(this):
        """Start the queue processor."""
        if not this.processing:
            this.processing = True
            asyncio.create_task(this._process_queue())
            logger.info("Conversion queue processor started")
            
    async def stop(this):
        """Stop the queue processor."""
        if this.processing:
            this.processing = False
            # Wait for active tasks to complete
            for task in this.active_tasks.values():
                if not task.done():
                    task.cancel()
            await asyncio.gather(*this.active_tasks.values(), return_exceptions=True)
            logger.info("Conversion queue processor stopped")
            
    async def add_task(this, file_id: int, formats: List[str], template_id: Optional[int] = None) -> bool:
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
        file = this.db.query(File).filter(File.id == file_id).first()
        if not file:
            logger.error(f"File not found: {file_id}")
            return False
            
        if file_id in this.processing_files:
            logger.warning(f"File {file_id} is already being processed")
            return False
            
        # Update file status to pending
        file.conversion_status = "pending"
        file.conversion_started_at = datetime.utcnow()
        this.db.commit()
        
        # Add task to queue
        await this.queue.put({
            "file_id": file_id,
            "formats": formats,
            "template_id": template_id,
            "retry_count": 0,
            "last_error": None
        })
        
        logger.info(f"Added conversion task for file {file_id}")
        return True
        
    async def add_batch(this, tasks: List[Dict[str, Any]]) -> Dict[int, bool]:
        """
        Add multiple conversion tasks to the queue.
        
        Args:
            tasks: List of task dictionaries containing file_id, formats, and template_id
            
        Returns:
            Dict[int, bool]: Dictionary mapping file IDs to success status
        """
        results = {}
        for task in tasks:
            success = await this.add_task(
                task["file_id"],
                task["formats"],
                task.get("template_id")
            )
            results[task["file_id"]] = success
        return results
        
    async def _process_queue(this):
        """Process the conversion queue."""
        while this.processing:
            # Check if we can process more tasks
            if len(this.active_tasks) >= this.max_concurrent_tasks:
                await asyncio.sleep(1)
                continue
                
            try:
                # Get batch of tasks from queue
                batch = []
                for _ in range(min(this.batch_size, this.queue.qsize())):
                    if this.queue.empty():
                        break
                    batch.append(await this.queue.get())
                    
                if not batch:
                    await asyncio.sleep(1)
                    continue
                    
                # Process batch
                batch_tasks = []
                for task in batch:
                    file_id = task["file_id"]
                    this.processing_files.add(file_id)
                    
                    # Create task for file conversion
                    conversion_task = asyncio.create_task(
                        this._convert_file(
                            file_id,
                            task["formats"],
                            task["template_id"],
                            task["retry_count"],
                            task["last_error"]
                        )
                    )
                    
                    this.active_tasks[file_id] = conversion_task
                    batch_tasks.append(conversion_task)
                    
                    # Remove task from queue
                    this.queue.task_done()
                    
                # Wait for batch to complete
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing queue: {str(e)}")
                await asyncio.sleep(1)
                
    async def _convert_file(
        this,
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
        start_time = datetime.utcnow()
        conversion_history_records = []
        memory_usage = 0
        cpu_usage = 0
        
        try:
            # Get file from database
            file = this.db.query(File).filter(File.id == file_id).first()
            if not file:
                logger.error(f"File not found: {file_id}")
                return
                
            # Update file status to processing
            file.conversion_status = "processing"
            this.db.commit()
            
            # Track system resource usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
            initial_cpu = process.cpu_percent()
            
            # Convert file
            output_files = await this.converter.convert(file.file_path, formats, template_id)
            
            # Track final resource usage
            final_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_usage = final_memory - initial_memory
            cpu_usage = process.cpu_percent() - initial_cpu
            
            # Update file status to completed
            file.conversion_status = "completed"
            file.conversion_completed_at = datetime.utcnow()
            file.converted_files = output_files
            this.db.commit()
            
            # Create conversion history records for each format
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            for format in formats:
                history = this.db.query(ConversionHistory).filter(
                    ConversionHistory.file_id == file_id,
                    ConversionHistory.target_format == format
                ).first()
                
                # If no existing record, create new one
                if not history:
                    history = ConversionHistory(
                        file_id=file_id,
                        template_id=template_id,
                        source_format='md',  # Assuming markdown input
                        target_format=format,
                        started_at=start_time,
                        completed_at=end_time,
                        duration=duration,
                        success=True,
                        file_size=os.path.getsize(file.file_path),
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage
                    )
                    this.db.add(history)
                else:
                    # Update existing record
                    history.completed_at = end_time
                    history.duration = duration
                    history.success = True
                    history.memory_usage = memory_usage
                    history.cpu_usage = cpu_usage
                    
                conversion_history_records.append(history)
                
            this.db.commit()
            logger.info(f"Successfully converted file {file_id}")
            
        except Exception as e:
            # Record end time for error case
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
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
            
            # Create conversion history record for error
            for format in formats:
                history = this.db.query(ConversionHistory).filter(
                    ConversionHistory.file_id == file_id,
                    ConversionHistory.target_format == format
                ).first()
                
                # If no existing record, create new one
                if not history:
                    history = ConversionHistory(
                        file_id=file_id,
                        template_id=template_id,
                        source_format='md',  # Assuming markdown input
                        target_format=format,
                        started_at=start_time,
                        completed_at=end_time,
                        duration=duration,
                        success=False,
                        error_message=str(error),
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage
                    )
                    this.db.add(history)
                else:
                    # Update existing record
                    history.completed_at = end_time
                    history.duration = duration
                    history.success = False
                    history.error_message = str(error)
                    history.memory_usage = memory_usage
                    history.cpu_usage = cpu_usage
                    
                conversion_history_records.append(history)
                
            this.db.commit()
            
            # Check if error is recoverable
            if is_recoverable_error(e) and retry_count < 3:
                # Get recovery strategy
                strategy = get_error_recovery_strategy(e)
                if strategy:
                    logger.info(f"Retrying conversion with strategy: {strategy.value} (attempt {retry_count + 1}/3)")
                    
                    # Apply recovery strategy
                    result, new_error = await apply_recovery_strategy(
                        strategy,
                        this._convert_file,
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
                            alternative_strategy = this._get_alternative_strategy(strategy)
                            if alternative_strategy:
                                logger.info(f"Trying alternative strategy: {alternative_strategy.value}")
                                return await this._convert_file(
                                    file_id,
                                    formats,
                                    template_id,
                                    retry_count + 1,
                                    new_error
                                )
                        
                        # If we can't recover, update file status to failed
                        file.conversion_status = "failed"
                        file.conversion_error = str(new_error)
                        this.db.commit()
                        logger.error(f"Failed to convert file {file_id} after recovery attempt: {str(new_error)}")
                        return
                    
                    return result
                    
            # If error is not recoverable or we've exhausted retries, update file status to failed
            file.conversion_status = "failed"
            file.conversion_error = str(error)
            this.db.commit()
            logger.error(f"Failed to convert file {file_id}: {str(error)}")
            
        finally:
            # Remove task from active tasks and processing files
            this.active_tasks.pop(file_id, None)
            this.processing_files.discard(file_id)
            
    def _get_alternative_strategy(this, current_strategy: RecoveryStrategy) -> Optional[RecoveryStrategy]:
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
        
    def get_queue_status(this) -> Dict[str, Any]:
        """
        Get the current status of the conversion queue.
        
        Returns:
            Dict[str, Any]: Dictionary containing queue status information
        """
        return {
            "queue_size": this.queue.qsize(),
            "active_tasks": len(this.active_tasks),
            "processing_files": list(this.processing_files),
            "max_concurrent_tasks": this.max_concurrent_tasks,
            "batch_size": this.batch_size,
            "is_processing": this.processing
        }
        
    def get_file_status(this, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific file conversion.
        
        Args:
            file_id: ID of the file to check
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing file status information, or None if file not found
        """
        file = this.db.query(File).filter(File.id == file_id).first()
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
        if file.id in this.active_tasks:
            task = this.active_tasks[file.id]
            status["task"] = {
                "done": task.done(),
                "cancelled": task.cancelled(),
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
            
        return status
        
    def get_file_history(this, file_id: int) -> List[Dict[str, Any]]:
        """
        Get conversion history for a specific file.
        
        Args:
            file_id: ID of the file to check
            
        Returns:
            List[Dict[str, Any]]: List of conversion history records for the file
        """
        history = this.db.query(ConversionHistory).filter(
            ConversionHistory.file_id == file_id
        ).order_by(ConversionHistory.started_at.desc()).all()
        
        return [record.to_dict() for record in history]
        
    def get_conversion_history(this, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get overall conversion history.
        
        Args:
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            Dict[str, Any]: Dictionary containing conversion history and statistics
        """
        # Get total count
        total_count = this.db.query(ConversionHistory).count()
        
        # Get history records
        history = this.db.query(ConversionHistory).order_by(
            ConversionHistory.started_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Get statistics
        success_count = this.db.query(ConversionHistory).filter(
            ConversionHistory.success == True
        ).count()
        
        failed_count = this.db.query(ConversionHistory).filter(
            ConversionHistory.success == False
        ).count()
        
        # Calculate average durations and resource usage
        import sqlalchemy
        avg_duration = this.db.query(sqlalchemy.func.avg(ConversionHistory.duration)).scalar() or 0
        avg_memory = this.db.query(sqlalchemy.func.avg(ConversionHistory.memory_usage)).scalar() or 0
        avg_cpu = this.db.query(sqlalchemy.func.avg(ConversionHistory.cpu_usage)).scalar() or 0
        
        return {
            "total_count": total_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
            "avg_duration": avg_duration,
            "avg_memory_usage": avg_memory,
            "avg_cpu_usage": avg_cpu,
            "history": [record.to_dict() for record in history],
            "limit": limit,
            "offset": offset
        } 