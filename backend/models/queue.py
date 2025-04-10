from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class QueueItem(BaseModel):
    """
    Represents an item in the conversion queue.
    """
    id: str
    file_id: str
    file_name: str
    input_format: str
    output_format: str
    status: str = "pending"
    progress: float = 0.0
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)

class QueueStatus(BaseModel):
    """
    Represents the current status of the conversion queue.
    """
    size: int = 0
    completed: int = 0
    failed: int = 0
    processing: int = 0
    total_processed: int = 0
    avg_processing_time: Optional[float] = None
    last_error: Optional[str] = None

class ConversionHistoryItem(BaseModel):
    """
    Represents an item in the conversion history.
    """
    id: str
    file_id: str
    file_name: str
    output_format: str
    status: str
    timestamp: datetime
    duration: Optional[float] = None  # in seconds
    error: Optional[str] = None
    user_id: str
    options: Dict[str, Any] = Field(default_factory=dict)

class SystemMetrics(BaseModel):
    """
    Represents system metrics for monitoring.
    """
    cpuUsage: float
    memoryUsage: float
    diskUsage: float
    uptime: int  # in seconds
    activeWorkers: int = 0
    queueBacklog: int = 0
    avgResponseTime: Optional[float] = None  # in milliseconds

class BatchConversionRequest(BaseModel):
    """
    Represents a batch of conversion requests.
    """
    tasks: List[Dict[str, Any]]
    priority: Optional[int] = None 