"""
Project management router for Markdown Forge.
This module handles project operation endpoints.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User, Project
from auth import get_current_active_user

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    """Schema for project creation."""
    name: str
    description: str | None = None

class ProjectUpdate(BaseModel):
    """Schema for project update."""
    name: str | None = None
    description: str | None = None

class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: str
    updated_at: str | None

    class Config:
        """Pydantic config."""
        from_attributes = True

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new project.
    
    Args:
        project_data (ProjectCreate): Project creation data
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        ProjectResponse: Created project data
    """
    # Check if project name exists for user
    if db.query(Project).filter(
        Project.name == project_data.name,
        Project.owner_id == current_user.id
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name already exists"
        )
    
    # Create project
    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List user's projects.
    
    Args:
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        List[ProjectResponse]: List of user's projects
    """
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get project details.
    
    Args:
        project_id (int): ID of the project
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        ProjectResponse: Project data
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update a project.
    
    Args:
        project_id (int): ID of the project to update
        project_data (ProjectUpdate): Updated project data
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        ProjectResponse: Updated project data
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if new name exists
    if project_data.name and project_data.name != project.name:
        if db.query(Project).filter(
            Project.name == project_data.name,
            Project.owner_id == current_user.id
        ).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project name already exists"
            )
    
    # Update project
    if project_data.name:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    
    db.commit()
    db.refresh(project)
    
    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a project.
    
    Args:
        project_id (int): ID of the project to delete
        current_user (User): Current authenticated user
        db (Session): Database session
        
    Returns:
        dict: Success message
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"} 