"""
API endpoints for agents.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson.objectid import ObjectId

from ...services.agent_service import AgentService
from ..schemas import AgentCreate, AgentUpdate, AgentResponse, PaginatedResponse, AgentStatus
from ..dependencies import get_agent_service

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={404: {"description": "Agent not found"}},
)


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent: AgentCreate, service: AgentService = Depends(get_agent_service)):
    """Create a new agent."""
    try:
        created_agent = await service.create(**agent.model_dump())
        return created_agent
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create agent: {str(e)}",
        )


@router.get("/", response_model=PaginatedResponse[AgentResponse])
async def get_agents(
    skip: int = 0, 
    limit: int = 100, 
    agent_type: Optional[str] = None,
    agent_status: Optional[str] = None,
    service: AgentService = Depends(get_agent_service)
):
    """Get all agents with pagination and optional filtering."""
    # Build filter
    filters = {}
    if agent_type:
        filters["agent_type"] = agent_type
    if agent_status:
        filters["status"] = agent_status

    # Get agents and count
    agents = await service.get_all(skip=skip, limit=limit, filters=filters)
    total = await service.count(filters=filters)
    
    return {
        "data": agents,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, service: AgentService = Depends(get_agent_service)):
    """Get an agent by ID."""
    try:
        agent = await service.get_by_id(ObjectId(agent_id))
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found",
            )
        return agent
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve agent: {str(e)}",
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str, agent: AgentUpdate, service: AgentService = Depends(get_agent_service)
):
    """Update an agent."""
    try:
        updated_agent = await service.update(
            id=ObjectId(agent_id), 
            **agent.model_dump(exclude_unset=True)
        )
        if not updated_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found",
            )
        return updated_agent
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update agent: {str(e)}",
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, service: AgentService = Depends(get_agent_service)):
    """Delete an agent."""
    try:
        result = await service.delete(ObjectId(agent_id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found",
            )
        return None
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete agent: {str(e)}",
        )