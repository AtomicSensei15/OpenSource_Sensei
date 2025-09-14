"""
API endpoints for analyses.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson.objectid import ObjectId

from ...services.analysis_service import AnalysisService
from ..schemas import AnalysisCreate, AnalysisUpdate, AnalysisResponse, PaginatedResponse, AnalysisStatus
from ..dependencies import get_analysis_service

router = APIRouter(
    prefix="/analyses",
    tags=["analyses"],
    responses={404: {"description": "Analysis not found"}},
)


@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(analysis: AnalysisCreate, service: AnalysisService = Depends(get_analysis_service)):
    """Create a new analysis."""
    try:
        created_analysis = await service.create(**analysis.model_dump())
        return created_analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create analysis: {str(e)}",
        )


@router.get("/", response_model=PaginatedResponse[AnalysisResponse])
async def get_analyses(
    skip: int = 0, 
    limit: int = 100, 
    project_id: Optional[str] = None,
    analysis_status: Optional[str] = None,
    service: AnalysisService = Depends(get_analysis_service)
):
    """Get all analyses with pagination and optional filtering."""
    # Build filter
    filters = {}
    if project_id:
        filters["project_id"] = ObjectId(project_id)
    if analysis_status:
        filters["status"] = analysis_status

    # Get analyses and count
    analyses = await service.get_all(skip=skip, limit=limit, filters=filters)
    total = await service.count(filters=filters)
    
    return {
        "data": analyses,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str, service: AnalysisService = Depends(get_analysis_service)):
    """Get an analysis by ID."""
    try:
        analysis = await service.get_by_id(ObjectId(analysis_id))
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID {analysis_id} not found",
            )
        return analysis
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve analysis: {str(e)}",
        )


@router.put("/{analysis_id}", response_model=AnalysisResponse)
async def update_analysis(
    analysis_id: str, analysis: AnalysisUpdate, service: AnalysisService = Depends(get_analysis_service)
):
    """Update an analysis."""
    try:
        updated_analysis = await service.update(
            id=ObjectId(analysis_id), 
            **analysis.model_dump(exclude_unset=True)
        )
        if not updated_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID {analysis_id} not found",
            )
        return updated_analysis
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update analysis: {str(e)}",
        )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(analysis_id: str, service: AnalysisService = Depends(get_analysis_service)):
    """Delete an analysis."""
    try:
        result = await service.delete(ObjectId(analysis_id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID {analysis_id} not found",
            )
        return None
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete analysis: {str(e)}",
        )