"""
API endpoints for tasks.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson.objectid import ObjectId

from ...services.task_service import TaskService
from ..schemas import TaskCreate, TaskUpdate, TaskResponse, PaginatedResponse, TaskStatus
from ..dependencies import get_task_service

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Task not found"}},
)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, service: TaskService = Depends(get_task_service)):
    """Create a new task."""
    try:
        created_task = await service.create(**task.model_dump())
        return created_task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create task: {str(e)}",
        )


@router.get("/", response_model=PaginatedResponse[TaskResponse])
async def get_tasks(
    skip: int = 0, 
    limit: int = 100, 
    analysis_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    task_status: Optional[str] = None,
    service: TaskService = Depends(get_task_service)
):
    """Get all tasks with pagination and optional filtering."""
    # Build filter
    filters = {}
    if analysis_id:
        filters["analysis_id"] = ObjectId(analysis_id)
    if agent_id:
        filters["agent_id"] = ObjectId(agent_id)
    if task_status:
        filters["status"] = task_status

    # Get tasks and count
    tasks = await service.get_all(skip=skip, limit=limit, filters=filters)
    total = await service.count(filters=filters)
    
    return {
        "data": tasks,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, service: TaskService = Depends(get_task_service)):
    """Get a task by ID."""
    try:
        task = await service.get_by_id(ObjectId(task_id))
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )
        return task
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve task: {str(e)}",
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, task: TaskUpdate, service: TaskService = Depends(get_task_service)
):
    """Update a task."""
    try:
        updated_task = await service.update(
            id=ObjectId(task_id), 
            **task.model_dump(exclude_unset=True)
        )
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )
        return updated_task
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update task: {str(e)}",
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, service: TaskService = Depends(get_task_service)):
    """Delete a task."""
    try:
        result = await service.delete(ObjectId(task_id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )
        return None
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete task: {str(e)}",
        )