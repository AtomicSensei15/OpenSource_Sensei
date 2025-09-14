"""
Project API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson.objectid import ObjectId

from ...services.project_service import ProjectService
from ..schemas import ProjectCreate, ProjectUpdate, ProjectResponse, PaginatedResponse, ProjectStatus
from ..dependencies import get_project_service

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Project not found"}},
)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, service: ProjectService = Depends(get_project_service)):
    """Create a new project."""
    try:
        return await service.create(**project.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create project: {str(e)}",
        )


@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def get_projects(
    skip: int = 0, 
    limit: int = 100, 
    name: Optional[str] = None,
    project_status: Optional[str] = None,
    service: ProjectService = Depends(get_project_service)
):
    """Get all projects with pagination and optional filtering."""
    # Build filter
    filters = {}
    if name:
        filters["name"] = {"$regex": name, "$options": "i"}
    if project_status:
        filters["status"] = project_status

    # Get projects and count
    projects = await service.get_all(skip=skip, limit=limit, filters=filters)
    total = await service.count(filters=filters)
    
    return {
        "data": projects,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, service: ProjectService = Depends(get_project_service)):
    """Get a project by ID."""
    try:
        project = await service.get_by_id(ObjectId(project_id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )
        return project
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve project: {str(e)}",
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, project: ProjectUpdate, service: ProjectService = Depends(get_project_service)
):
    """Update a project."""
    try:
        updated_project = await service.update(
            id=ObjectId(project_id), 
            **project.model_dump(exclude_unset=True)
        )
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )
        return updated_project
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update project: {str(e)}",
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, service: ProjectService = Depends(get_project_service)):
    """Delete a project."""
    try:
        result = await service.delete(ObjectId(project_id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )
        return None
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete project: {str(e)}",
        )


@router.post("/{project_id}/analyze", response_model=ProjectResponse)
async def start_project_analysis(project_id: str, service: ProjectService = Depends(get_project_service)):
    """Start the analysis of a project."""
    try:
        # Get the project
        project = await service.get_by_id(ObjectId(project_id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )
        
        # Update status to analyzing
        updated_project = await service.update(
            id=ObjectId(project_id), 
            status=ProjectStatus.ANALYZING
        )
        
        # Here you would typically trigger a background task for analysis
        # For now, we'll just return the updated project
        return updated_project
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start analysis: {str(e)}",
        )