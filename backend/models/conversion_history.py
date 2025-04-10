"""
Conversion history model for tracking conversion jobs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..database import Base

class ConversionHistory(Base):
    """
    Model for tracking conversion history of files.
    
    Attributes:
        id (int): Primary key
        file_id (int): ID of the file being converted (foreign key)
        output_format (str): Output format of the conversion (e.g., "html", "pdf")
        started_at (datetime): When the conversion started
        completed_at (datetime): When the conversion completed
        duration (float): Duration of the conversion in seconds
        success (bool): Whether the conversion was successful
        error_message (str): Error message if conversion failed
        conversion_options (JSON): Options used for the conversion
        memory_usage (float): Memory usage during conversion (MB)
        cpu_usage (float): CPU usage during conversion (%)
    """
    __tablename__ = "conversion_history"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))
    output_format = Column(String, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)
    success = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    conversion_options = Column(JSON, nullable=True)
    memory_usage = Column(Float, nullable=True)
    cpu_usage = Column(Float, nullable=True)
    template_id = Column(Integer, ForeignKey("templates.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="conversion_history")
    template = relationship("Template", back_populates="conversion_history")
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "output_format": self.output_format,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "success": self.success,
            "error_message": self.error_message,
            "conversion_options": self.conversion_options,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "template_id": self.template_id
        } 