"""
Template management router for Markdown Forge.
This module provides endpoints for managing conversion templates.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..services.template_manager import TemplateManager
from ..utils.error_handler import AppError

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/templates",
    tags=["templates"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models for request/response
class TemplateBase(BaseModel):
    """Base model for template data."""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    is_public: bool = Field(False, description="Whether the template is public")
    pandoc_options: Optional[Dict[str, Any]] = Field(None, description="Pandoc options")
    html_template: Optional[str] = Field(None, description="Path to HTML template")
    pdf_template: Optional[str] = Field(None, description="Path to PDF template")
    docx_template: Optional[str] = Field(None, description="Path to DOCX template")
    css_file: Optional[str] = Field(None, description="Path to CSS file")

class TemplateCreate(TemplateBase):
    """Model for creating a template."""
    pass

class TemplateUpdate(BaseModel):
    """Model for updating a template."""
    name: Optional[str] = Field(None, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    is_public: Optional[bool] = Field(None, description="Whether the template is public")
    pandoc_options: Optional[Dict[str, Any]] = Field(None, description="Pandoc options")
    html_template: Optional[str] = Field(None, description="Path to HTML template")
    pdf_template: Optional[str] = Field(None, description="Path to PDF template")
    docx_template: Optional[str] = Field(None, description="Path to DOCX template")
    css_file: Optional[str] = Field(None, description="Path to CSS file")

class TemplateResponse(TemplateBase):
    """Model for template response."""
    id: int
    owner_id: int
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True

class TemplateList(BaseModel):
    """Model for list of templates."""
    templates: List[TemplateResponse]
    total: int

# Dependency for template manager
def get_template_manager(db: Session = Depends(get_db)) -> TemplateManager:
    """Get template manager instance."""
    return TemplateManager(db)

@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """
    Create a new conversion template.
    
    Args:
        template: Template data
        db: Database session
        template_manager: Template manager service
        
    Returns:
        TemplateResponse: Created template
    """
    try:
        # TODO: Get current user ID from authentication
        user_id = 1  # Placeholder for now
        
        # Create template
        created_template = template_manager.create_template(
            name=template.name,
            owner_id=user_id,
            description=template.description,
            is_public=template.is_public,
            pandoc_options=template.pandoc_options,
            html_template=template.html_template,
            pdf_template=template.pdf_template,
            docx_template=template.docx_template,
            css_file=template.css_file
        )
        
        return created_template
        
    except AppError as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error creating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )

@router.get("/", response_model=TemplateList)
async def list_templates(
    db: Session = Depends(get_db),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """
    List all templates accessible to the current user.
    
    Args:
        db: Database session
        template_manager: Template manager service
        
    Returns:
        TemplateList: List of templates
    """
    try:
        # TODO: Get current user ID from authentication
        user_id = 1  # Placeholder for now
        
        # Get user's templates
        user_templates = template_manager.get_user_templates(user_id)
        
        # Get public templates
        public_templates = template_manager.get_public_templates()
        
        # Combine and deduplicate
        all_templates = list(set(user_templates + public_templates))
        
        return {
            "templates": all_templates,
            "total": len(all_templates)
        }
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """
    Get a template by ID.
    
    Args:
        template_id: ID of the template
        db: Database session
        template_manager: Template manager service
        
    Returns:
        TemplateResponse: Template data
    """
    try:
        # TODO: Get current user ID from authentication
        user_id = 1  # Placeholder for now
        
        # Get template
        template = template_manager.get_template(template_id, user_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found or not accessible"
            )
            
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template: TemplateUpdate,
    db: Session = Depends(get_db),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """
    Update a template.
    
    Args:
        template_id: ID of the template
        template: Updated template data
        db: Database session
        template_manager: Template manager service
        
    Returns:
        TemplateResponse: Updated template
    """
    try:
        # TODO: Get current user ID from authentication
        user_id = 1  # Placeholder for now
        
        # Update template
        updated_template = template_manager.update_template(
            template_id=template_id,
            user_id=user_id,
            name=template.name,
            description=template.description,
            is_public=template.is_public,
            pandoc_options=template.pandoc_options,
            html_template=template.html_template,
            pdf_template=template.pdf_template,
            docx_template=template.docx_template,
            css_file=template.css_file
        )
        
        if not updated_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found or not accessible"
            )
            
        return updated_template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """
    Delete a template.
    
    Args:
        template_id: ID of the template
        db: Database session
        template_manager: Template manager service
    """
    try:
        # TODO: Get current user ID from authentication
        user_id = 1  # Placeholder for now
        
        # Delete template
        success = template_manager.delete_template(template_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found or not accessible"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )

@router.get("/{template_id}/options/{format}", response_model=Dict[str, Any])
async def get_template_options(
    template_id: int,
    format: str,
    db: Session = Depends(get_db),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """
    Get Pandoc options for a template and format.
    
    Args:
        template_id: ID of the template
        format: Output format
        db: Database session
        template_manager: Template manager service
        
    Returns:
        Dict[str, Any]: Pandoc options
    """
    try:
        # Get template options
        options = template_manager.get_template_options(template_id, format)
        return options
        
    except Exception as e:
        logger.error(f"Error getting template options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template options: {str(e)}"
        ) 