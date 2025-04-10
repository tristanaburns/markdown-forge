"""
Database models for Markdown Forge.
This module defines SQLAlchemy models for users, projects, and files.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class User(Base):
    """User model for authentication and user management."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="owner")
    templates = relationship("Template", back_populates="owner")

class Document(Base):
    """Document model for storing markdown documents."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="documents")

class Template(Base):
    """Template model for storing markdown templates."""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="templates")

class Project(Base):
    """Project model for organizing documentation."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="projects")
    files = relationship("File", back_populates="project")

class ConversionStatus(enum.Enum):
    """Enum for file conversion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class File(Base):
    """File model for storing markdown and converted files."""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # md, pdf, docx, html, png
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Conversion status fields
    conversion_status = Column(Enum(ConversionStatus), default=ConversionStatus.PENDING)
    conversion_error = Column(String, nullable=True)
    converted_files = Column(String, nullable=True)  # JSON string of converted file paths
    conversion_started_at = Column(DateTime(timezone=True), nullable=True)
    conversion_completed_at = Column(DateTime(timezone=True), nullable=True)
    template_id = Column(Integer, ForeignKey("conversion_templates.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="files")
    owner = relationship("User", back_populates="files")
    template = relationship("ConversionTemplate", back_populates="files")

class ConversionTemplate(Base):
    """Template model for file conversion settings."""
    __tablename__ = "conversion_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Template settings
    pandoc_options = Column(Text, nullable=True)  # JSON string of Pandoc options
    html_template = Column(String, nullable=True)  # Path to HTML template
    pdf_template = Column(String, nullable=True)  # Path to PDF template
    docx_template = Column(String, nullable=True)  # Path to DOCX template
    css_file = Column(String, nullable=True)  # Path to CSS file
    
    # Relationships
    owner = relationship("User", back_populates="templates")
    files = relationship("File", back_populates="template") 