"""
Conversion queue implementation for handling file conversions.
This module provides a queue-based system for managing file conversions with
concurrent processing capabilities and performance monitoring.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
import psutil
from sqlalchemy.orm import Session
from .models import File, ConversionTemplate, ConversionHistory

logger = logging.getLogger(__name__)

class ConversionQueue:
    """Queue for managing file conversions with concurrent processing."""
    
    def __init__(self, db: Session, batch_size: int = 5):
        """
        Initialize the conversion queue.
        
        Args:
            db: SQLAlchemy database session
            batch_size: Number of files to process concurrently
        """
        self.db = db
        self.batch_size = batch_size
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processing_files: Set[int] = set()
        self.active_tasks: Set[asyncio.Task] = set()
        
    async def add_task(self, file_id: int, template_id: Optional[int] = None) -> None:
        """
        Add a file conversion task to the queue.
        
        Args:
            file_id: ID of the file to convert
            template_id: Optional ID of the template to use
        """
        await self.queue.put((file_id, template_id))
        logger.info(f"Added file {file_id} to conversion queue")
        
    async def add_batch(self, file_ids: List[int], template_id: Optional[int] = None) -> None:
        """
        Add multiple files to the conversion queue.
        
        Args:
            file_ids: List of file IDs to convert
            template_id: Optional ID of the template to use
        """
        for file_id in file_ids:
            await self.add_task(file_id, template_id)
        logger.info(f"Added {len(file_ids)} files to conversion queue")
        
    async def _process_file(self, file_id: int, template_id: Optional[int] = None) -> None:
        """
        Process a single file conversion.
        
        Args:
            file_id: ID of the file to convert
            template_id: Optional ID of the template to use
        """
        try:
            # Get file and template from database
            file = self.db.query(File).filter(File.id == file_id).first()
            if not file:
                raise ValueError(f"File {file_id} not found")
                
            template = None
            if template_id:
                template = self.db.query(ConversionTemplate).filter(
                    ConversionTemplate.id == template_id
                ).first()
                
            # Create conversion history record
            history = ConversionHistory(
                file_id=file_id,
                template_id=template_id,
                source_format=file.format,
                target_format=template.target_format if template else "unknown",
                started_at=datetime.utcnow()
            )
            self.db.add(history)
            self.db.commit()
            
            # Start monitoring resources
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            start_cpu = process.cpu_percent()
            
            # Perform conversion
            # TODO: Implement actual conversion logic
            
            # Update history with results
            end_memory = process.memory_info().rss / 1024 / 1024
            end_cpu = process.cpu_percent()
            
            history.completed_at = datetime.utcnow()
            history.duration = (history.completed_at - history.started_at).total_seconds()
            history.success = True
            history.file_size = file.size
            history.memory_usage = end_memory - start_memory
            history.cpu_usage = (end_cpu + start_cpu) / 2
            
            self.db.commit()
            logger.info(f"Successfully converted file {file_id}")
            
        except Exception as e:
            logger.error(f"Error converting file {file_id}: {str(e)}")
            if history:
                history.completed_at = datetime.utcnow()
                history.duration = (history.completed_at - history.started_at).total_seconds()
                history.success = False
                history.error_message = str(e)
                self.db.commit()
            raise
            
        finally:
            self.processing_files.remove(file_id)
            
    async def _process_queue(self) -> None:
        """Process files in the queue concurrently."""
        while True:
            try:
                # Get batch of files
                batch = []
                for _ in range(self.batch_size):
                    try:
                        file_id, template_id = await self.queue.get()
                        batch.append((file_id, template_id))
                    except asyncio.QueueEmpty:
                        break
                        
                if not batch:
                    await asyncio.sleep(1)
                    continue
                    
                # Process batch concurrently
                tasks = []
                for file_id, template_id in batch:
                    if file_id not in self.processing_files:
                        self.processing_files.add(file_id)
                        task = asyncio.create_task(
                            self._process_file(file_id, template_id)
                        )
                        tasks.append(task)
                        self.active_tasks.add(task)
                        
                if tasks:
                    await asyncio.gather(*tasks)
                    
            except Exception as e:
                logger.error(f"Error processing queue: {str(e)}")
                await asyncio.sleep(1)
                
    def get_status(self) -> Dict:
        """
        Get the current status of the conversion queue.
        
        Returns:
            Dict containing queue statistics
        """
        return {
            "queue_size": self.queue.qsize(),
            "processing_files": list(self.processing_files),
            "active_tasks": len(self.active_tasks),
            "batch_size": self.batch_size
        }
        
    def get_file_history(self, file_id: int) -> List[Dict]:
        """
        Get conversion history for a specific file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            List of conversion history records
        """
        history = self.db.query(ConversionHistory).filter(
            ConversionHistory.file_id == file_id
        ).order_by(ConversionHistory.started_at.desc()).all()
        
        return [
            {
                "id": h.id,
                "template_id": h.template_id,
                "source_format": h.source_format,
                "target_format": h.target_format,
                "started_at": h.started_at,
                "completed_at": h.completed_at,
                "duration": h.duration,
                "success": h.success,
                "error_message": h.error_message,
                "file_size": h.file_size,
                "memory_usage": h.memory_usage,
                "cpu_usage": h.cpu_usage
            }
            for h in history
        ] 