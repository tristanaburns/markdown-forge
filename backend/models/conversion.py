from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class ConversionRequest(BaseModel):
    """
    Represents a request to convert a file from one format to another.
    """
    file_id: str
    input_format: str
    output_format: str
    options: Dict[str, Any] = Field(default_factory=dict)
    priority: Optional[int] = None

class ConversionResponse(BaseModel):
    """
    Response for a conversion request.
    """
    task_id: str
    status: str
    message: str
    result_url: Optional[str] = None
    error: Optional[str] = None

class ConversionStatus(BaseModel):
    """
    Status of a conversion task.
    """
    task_id: str
    file_id: str
    status: str
    progress: float = 0.0
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result_url: Optional[str] = None

class ConversionOption(BaseModel):
    """
    Represents a conversion option that can be used.
    """
    name: str
    description: str
    type: str  # e.g., "string", "boolean", "number", "select"
    default: Any = None
    required: bool = False
    options: Optional[List[str]] = None  # For select type

class ConversionFormat(BaseModel):
    """
    Represents a supported conversion format.
    """
    id: str
    name: str
    description: str
    file_extensions: List[str]
    mime_type: str
    supported_options: List[ConversionOption] = Field(default_factory=list)
    can_convert_to: List[str] = Field(default_factory=list)
    can_convert_from: List[str] = Field(default_factory=list)

class SupportedFormats(BaseModel):
    """
    List of all supported conversion formats.
    """
    formats: List[ConversionFormat]
    default_options: Dict[str, Any] = Field(default_factory=dict) 