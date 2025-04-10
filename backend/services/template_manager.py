"""
Template manager service for Markdown Forge.
This module handles the management of conversion templates.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from ..models import ConversionTemplate, User
from ..utils.error_handler import AppError

# Configure logging
logger = logging.getLogger(__name__)

class TemplateManager:
    """Service for managing conversion templates."""
    
    def __init__(self, db: Session, templates_dir: str = "templates"):
        """
        Initialize the template manager.
        
        Args:
            db: Database session
            templates_dir: Directory for storing template files
        """
        self.db = db
        self.templates_dir = templates_dir
        self._ensure_templates_dir()
        
    def _ensure_templates_dir(self):
        """Ensure the templates directory exists."""
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(os.path.join(self.templates_dir, "html"), exist_ok=True)
        os.makedirs(os.path.join(self.templates_dir, "pdf"), exist_ok=True)
        os.makedirs(os.path.join(self.templates_dir, "docx"), exist_ok=True)
        os.makedirs(os.path.join(self.templates_dir, "css"), exist_ok=True)
        
    def create_template(
        self,
        name: str,
        owner_id: int,
        description: Optional[str] = None,
        is_public: bool = False,
        pandoc_options: Optional[Dict[str, Any]] = None,
        html_template: Optional[str] = None,
        pdf_template: Optional[str] = None,
        docx_template: Optional[str] = None,
        css_file: Optional[str] = None
    ) -> ConversionTemplate:
        """
        Create a new conversion template.
        
        Args:
            name: Template name
            owner_id: ID of the template owner
            description: Template description
            is_public: Whether the template is public
            pandoc_options: Pandoc options as a dictionary
            html_template: Path to HTML template file
            pdf_template: Path to PDF template file
            docx_template: Path to DOCX template file
            css_file: Path to CSS file
            
        Returns:
            ConversionTemplate: Created template
        """
        try:
            # Check if user exists
            user = self.db.query(User).filter(User.id == owner_id).first()
            if not user:
                raise AppError(status_code=404, message="User not found")
                
            # Create template
            template = ConversionTemplate(
                name=name,
                owner_id=owner_id,
                description=description,
                is_public=is_public,
                pandoc_options=json.dumps(pandoc_options) if pandoc_options else None,
                html_template=html_template,
                pdf_template=pdf_template,
                docx_template=docx_template,
                css_file=css_file
            )
            
            # Save template
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"Created template: {template.id} - {template.name}")
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating template: {str(e)}")
            raise AppError(status_code=500, message=f"Failed to create template: {str(e)}")
            
    def get_template(self, template_id: int, user_id: int) -> Optional[ConversionTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: ID of the template
            user_id: ID of the user requesting the template
            
        Returns:
            Optional[ConversionTemplate]: Template if found and accessible
        """
        try:
            # Get template
            template = self.db.query(ConversionTemplate).filter(ConversionTemplate.id == template_id).first()
            if not template:
                return None
                
            # Check access
            if not template.is_public and template.owner_id != user_id:
                return None
                
            return template
            
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return None
            
    def get_user_templates(self, user_id: int) -> List[ConversionTemplate]:
        """
        Get all templates owned by a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[ConversionTemplate]: List of user's templates
        """
        try:
            return self.db.query(ConversionTemplate).filter(ConversionTemplate.owner_id == user_id).all()
        except Exception as e:
            logger.error(f"Error getting user templates: {str(e)}")
            return []
            
    def get_public_templates(self) -> List[ConversionTemplate]:
        """
        Get all public templates.
        
        Returns:
            List[ConversionTemplate]: List of public templates
        """
        try:
            return self.db.query(ConversionTemplate).filter(ConversionTemplate.is_public == True).all()
        except Exception as e:
            logger.error(f"Error getting public templates: {str(e)}")
            return []
            
    def update_template(
        self,
        template_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
        pandoc_options: Optional[Dict[str, Any]] = None,
        html_template: Optional[str] = None,
        pdf_template: Optional[str] = None,
        docx_template: Optional[str] = None,
        css_file: Optional[str] = None
    ) -> Optional[ConversionTemplate]:
        """
        Update a template.
        
        Args:
            template_id: ID of the template to update
            user_id: ID of the user updating the template
            name: New template name
            description: New template description
            is_public: New public status
            pandoc_options: New Pandoc options
            html_template: New HTML template path
            pdf_template: New PDF template path
            docx_template: New DOCX template path
            css_file: New CSS file path
            
        Returns:
            Optional[ConversionTemplate]: Updated template if successful
        """
        try:
            # Get template
            template = self.db.query(ConversionTemplate).filter(ConversionTemplate.id == template_id).first()
            if not template:
                return None
                
            # Check ownership
            if template.owner_id != user_id:
                return None
                
            # Update fields
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            if is_public is not None:
                template.is_public = is_public
            if pandoc_options is not None:
                template.pandoc_options = json.dumps(pandoc_options)
            if html_template is not None:
                template.html_template = html_template
            if pdf_template is not None:
                template.pdf_template = pdf_template
            if docx_template is not None:
                template.docx_template = docx_template
            if css_file is not None:
                template.css_file = css_file
                
            # Save changes
            template.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"Updated template: {template.id} - {template.name}")
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating template: {str(e)}")
            return None
            
    def delete_template(self, template_id: int, user_id: int) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: ID of the template to delete
            user_id: ID of the user deleting the template
            
        Returns:
            bool: True if successful
        """
        try:
            # Get template
            template = self.db.query(ConversionTemplate).filter(ConversionTemplate.id == template_id).first()
            if not template:
                return False
                
            # Check ownership
            if template.owner_id != user_id:
                return False
                
            # Delete template
            self.db.delete(template)
            self.db.commit()
            
            logger.info(f"Deleted template: {template_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting template: {str(e)}")
            return False
            
    def get_template_options(self, template_id: int, format: str) -> Dict[str, Any]:
        """
        Get Pandoc options for a template and format.
        
        Args:
            template_id: ID of the template
            format: Output format
            
        Returns:
            Dict[str, Any]: Pandoc options
        """
        try:
            # Get template
            template = self.db.query(ConversionTemplate).filter(ConversionTemplate.id == template_id).first()
            if not template or not template.pandoc_options:
                return {}
                
            # Parse options
            options = json.loads(template.pandoc_options)
            
            # Get format-specific options
            format_options = options.get(format, {})
            
            # Add template paths if available
            if format == "html" and template.html_template:
                format_options["template"] = template.html_template
            elif format == "pdf" and template.pdf_template:
                format_options["template"] = template.pdf_template
            elif format == "docx" and template.docx_template:
                format_options["template"] = template.docx_template
                
            # Add CSS if available
            if template.css_file and format in ["html", "pdf"]:
                format_options["css"] = template.css_file
                
            return format_options
            
        except Exception as e:
            logger.error(f"Error getting template options: {str(e)}")
            return {} 