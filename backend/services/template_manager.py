"""
Template manager service for Markdown Forge.
This module handles the management of conversion templates.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session

from ..models import ConversionTemplate, User
from ..utils.error_handler import AppError
from ..models.template import Template
from ..models.template_version import TemplateVersion
from ..services.file_service import FileService
from ..services.conversion_queue import ConversionQueue

# Configure logging
logger = logging.getLogger(__name__)

class TemplateManager:
    """Manages template operations with caching and optimized loading."""
    
    def __init__(self, db: Session, file_service: FileService, conversion_queue: ConversionQueue):
        """
        Initialize the template manager.
        
        Args:
            db: Database session
            file_service: File service instance
            conversion_queue: Conversion queue instance
        """
        self.db = db
        self.file_service = file_service
        self.conversion_queue = conversion_queue
        self._template_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=5)
        
    def _get_cache_key(self, template_id: str, version: Optional[str] = None) -> str:
        """Generate cache key for template."""
        return f"{template_id}:{version or 'latest'}"
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached template is still valid."""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]
        
    def _update_cache(self, template_id: str, data: Dict[str, Any], version: Optional[str] = None):
        """Update template cache with expiry."""
        cache_key = self._get_cache_key(template_id, version)
        self._template_cache[cache_key] = data
        self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
        
    def _clear_cache(self, template_id: Optional[str] = None):
        """Clear template cache."""
        if template_id:
            # Clear specific template cache
            keys_to_remove = [k for k in self._template_cache.keys() if k.startswith(f"{template_id}:")]
            for key in keys_to_remove:
                self._template_cache.pop(key, None)
                self._cache_expiry.pop(key, None)
        else:
            # Clear all cache
            self._template_cache.clear()
            self._cache_expiry.clear()
        
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
            
    async def get_template(self, template_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get template with caching.
        
        Args:
            template_id: Template ID
            version: Optional version number
            
        Returns:
            Template data
        """
        cache_key = self._get_cache_key(template_id, version)
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for template {template_id} version {version}")
            return self._template_cache[cache_key]
            
        # Load from database
        template = self.db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise ValueError(f"Template {template_id} not found")
            
        # Get version
        if version:
            template_version = self.db.query(TemplateVersion).filter(
                TemplateVersion.template_id == template_id,
                TemplateVersion.version == version
            ).first()
        else:
            template_version = self.db.query(TemplateVersion).filter(
                TemplateVersion.template_id == template_id
            ).order_by(TemplateVersion.version.desc()).first()
            
        if not template_version:
            raise ValueError(f"Version {version} not found for template {template_id}")
            
        # Load template data
        template_data = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "version": template_version.version,
            "content": template_version.content,
            "metadata": template_version.metadata,
            "created_at": template_version.created_at.isoformat(),
            "updated_at": template_version.updated_at.isoformat()
        }
        
        # Update cache
        self._update_cache(template_id, template_data, version)
        
        return template_data
        
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
            
    async def update_template(self, template_id: str, content: Optional[str] = None,
                            name: Optional[str] = None, description: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update a template.
        
        Args:
            template_id: Template ID
            content: Optional new content
            name: Optional new name
            description: Optional new description
            metadata: Optional new metadata
            
        Returns:
            Updated template data
        """
        try:
            template = self.db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise ValueError(f"Template {template_id} not found")
                
            # Update template
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
                
            # Get latest version
            latest_version = self.db.query(TemplateVersion).filter(
                TemplateVersion.template_id == template_id
            ).order_by(TemplateVersion.version.desc()).first()
            
            if not latest_version:
                raise ValueError(f"No version found for template {template_id}")
                
            # Create new version if content or metadata changed
            if content is not None or metadata is not None:
                new_version = TemplateVersion(
                    template_id=template_id,
                    version=str(float(latest_version.version) + 0.1),
                    content=content or latest_version.content,
                    metadata=metadata or latest_version.metadata
                )
                self.db.add(new_version)
                
            self.db.commit()
            
            # Clear cache for this template
            self._clear_cache(template_id)
            
            return await self.get_template(template_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update template: {str(e)}")
            raise
            
    async def delete_template(self, template_id: str):
        """
        Delete a template.
        
        Args:
            template_id: Template ID
        """
        try:
            template = self.db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise ValueError(f"Template {template_id} not found")
                
            # Delete template and versions
            self.db.query(TemplateVersion).filter(
                TemplateVersion.template_id == template_id
            ).delete()
            self.db.delete(template)
            self.db.commit()
            
            # Clear cache for this template
            self._clear_cache(template_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete template: {str(e)}")
            raise
            
    async def list_templates(self, include_versions: bool = False) -> List[Dict[str, Any]]:
        """
        List all templates.
        
        Args:
            include_versions: Whether to include version information
            
        Returns:
            List of templates
        """
        templates = self.db.query(Template).all()
        result = []
        
        for template in templates:
            template_data = {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
            
            if include_versions:
                versions = self.db.query(TemplateVersion).filter(
                    TemplateVersion.template_id == template.id
                ).order_by(TemplateVersion.version.desc()).all()
                
                template_data["versions"] = [{
                    "version": v.version,
                    "created_at": v.created_at.isoformat(),
                    "updated_at": v.updated_at.isoformat()
                } for v in versions]
                
            result.append(template_data)
            
        return result
            
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