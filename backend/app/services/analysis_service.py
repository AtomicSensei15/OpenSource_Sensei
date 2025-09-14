"""
Analysis service for managing analysis operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from ..models.analysis import Analysis, AnalysisType, AnalysisStatus
from ..models.project import Project
from .base_service import BaseService, NotFoundError, ValidationError
from ..core.logging import get_logger

logger = get_logger(__name__)


class AnalysisService(BaseService[Analysis]):
    """Service for managing analyses."""
    
    def __init__(self):
        super().__init__(Analysis)
    
    async def create_analysis(
        self,
        project_id: ObjectId,
        name: str,
        analysis_type: AnalysisType,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Analysis:
        """Create a new analysis."""
        try:
            # Verify project exists
            project = await Project.get(project_id)
            if not project:
                raise NotFoundError(f"Project {project_id} not found")
            
            # Create analysis
            analysis = await self.create(
                project_id=project_id,
                name=name,
                description=description,
                analysis_type=analysis_type,
                config=config or {},
                parameters=parameters or {},
                status=AnalysisStatus.PENDING
            )
            
            logger.info(f"Created analysis: {analysis.name} (ID: {analysis.id}) for project {project_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            raise
    
    async def start_analysis(
        self,
        analysis_id: ObjectId,
        agent_id: Optional[str] = None
    ) -> Analysis:
        """Start an analysis."""
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            raise NotFoundError(f"Analysis {analysis_id} not found")
        
        if analysis.status != AnalysisStatus.PENDING:
            raise ValidationError(f"Analysis is already {analysis.status}")
        
        try:
            await analysis.mark_started(agent_id)
            logger.info(f"Started analysis {analysis_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error starting analysis {analysis_id}: {e}")
            raise
    
    async def complete_analysis(
        self,
        analysis_id: ObjectId,
        results: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
        recommendations: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[float] = None,
        quality_score: Optional[float] = None,
        execution_time: Optional[float] = None
    ) -> Analysis:
        """Complete an analysis."""
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            raise NotFoundError(f"Analysis {analysis_id} not found")
        
        try:
            # Update results
            if results:
                analysis.results = results
            
            if summary:
                analysis.summary = summary
            
            if recommendations:
                analysis.recommendations = recommendations
            
            if confidence_score is not None:
                analysis.confidence_score = confidence_score
            
            if quality_score is not None:
                analysis.quality_score = quality_score
            
            # Mark as completed
            await analysis.mark_completed(execution_time)
            
            logger.info(f"Completed analysis {analysis_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error completing analysis {analysis_id}: {e}")
            raise
    
    async def fail_analysis(
        self,
        analysis_id: ObjectId,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Analysis:
        """Mark analysis as failed."""
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            raise NotFoundError(f"Analysis {analysis_id} not found")
        
        try:
            await analysis.mark_failed(error_message, error_details)
            logger.error(f"Failed analysis {analysis_id}: {error_message}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error marking analysis {analysis_id} as failed: {e}")
            raise
    
    async def update_progress(
        self,
        analysis_id: ObjectId,
        percentage: int,
        step: Optional[str] = None,
        files_processed: Optional[int] = None
    ) -> Analysis:
        """Update analysis progress."""
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            raise NotFoundError(f"Analysis {analysis_id} not found")
        
        try:
            await analysis.update_progress(percentage, step)
            
            if files_processed is not None:
                analysis.files_processed = files_processed
                await analysis.save()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error updating progress for analysis {analysis_id}: {e}")
            raise
    
    async def get_analyses_by_project(
        self,
        project_id: ObjectId,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """Get all analyses for a project."""
        return await self.get_all(skip=skip, limit=limit, filters={"project_id": project_id})
    
    async def get_analyses_by_type(
        self,
        analysis_type: AnalysisType,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """Get analyses by type."""
        return await self.get_all(skip=skip, limit=limit, filters={"analysis_type": analysis_type})
    
    async def get_analyses_by_status(
        self,
        status: AnalysisStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """Get analyses by status."""
        return await self.get_all(skip=skip, limit=limit, filters={"status": status})
    
    async def get_running_analyses(self) -> List[Analysis]:
        """Get all currently running analyses."""
        return await self.get_analyses_by_status(AnalysisStatus.RUNNING)
    
    async def get_pending_analyses(self) -> List[Analysis]:
        """Get all pending analyses."""
        return await self.get_analyses_by_status(AnalysisStatus.PENDING)
    
    async def cancel_analysis(self, analysis_id: ObjectId) -> Analysis:
        """Cancel a running or pending analysis."""
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            raise NotFoundError(f"Analysis {analysis_id} not found")
        
        if analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]:
            raise ValidationError(f"Cannot cancel analysis in status {analysis.status}")
        
        try:
            await analysis.mark_cancelled()
            logger.info(f"Cancelled analysis {analysis_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error cancelling analysis {analysis_id}: {e}")
            raise
    
    async def get_analysis_statistics(self, analysis_id: ObjectId) -> Dict[str, Any]:
        """Get analysis statistics."""
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            raise NotFoundError(f"Analysis {analysis_id} not found")
        
        try:
            stats = {
                "analysis_id": analysis.id,
                "name": analysis.name,
                "type": analysis.analysis_type,
                "status": analysis.status,
                "progress_percentage": analysis.progress_percentage,
                "files_processed": analysis.files_processed,
                "files_total": analysis.files_total,
                "files_skipped": analysis.files_skipped,
                "confidence_score": analysis.confidence_score,
                "quality_score": analysis.quality_score,
                "execution_time_seconds": analysis.execution_time_seconds,
                "memory_usage_mb": analysis.memory_usage_mb,
                "tokens_used": analysis.tokens_used,
                "started_at": analysis.started_at,
                "completed_at": analysis.completed_at,
                "duration_seconds": analysis.duration_seconds,
                "success_rate": analysis.success_rate,
                "is_completed": analysis.is_completed,
                "is_running": analysis.is_running
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics for analysis {analysis_id}: {e}")
            return {}
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide analysis statistics."""
        try:
            all_analyses = await self.get_all()
            
            stats = {
                "total_analyses": len(all_analyses),
                "pending_analyses": 0,
                "running_analyses": 0,
                "completed_analyses": 0,
                "failed_analyses": 0,
                "cancelled_analyses": 0,
                "analyses_by_type": {},
                "average_confidence_score": 0.0,
                "average_quality_score": 0.0,
                "average_execution_time": 0.0,
                "total_files_processed": 0,
                "total_tokens_used": 0
            }
            
            confidence_scores = []
            quality_scores = []
            execution_times = []
            
            for analysis in all_analyses:
                # Count by status
                if analysis.status == AnalysisStatus.PENDING:
                    stats["pending_analyses"] += 1
                elif analysis.status == AnalysisStatus.RUNNING:
                    stats["running_analyses"] += 1
                elif analysis.status == AnalysisStatus.COMPLETED:
                    stats["completed_analyses"] += 1
                elif analysis.status == AnalysisStatus.FAILED:
                    stats["failed_analyses"] += 1
                elif analysis.status == AnalysisStatus.CANCELLED:
                    stats["cancelled_analyses"] += 1
                
                # Count by type
                analysis_type_str = analysis.analysis_type.value if hasattr(analysis.analysis_type, 'value') else str(analysis.analysis_type)
                if analysis_type_str not in stats["analyses_by_type"]:
                    stats["analyses_by_type"][analysis_type_str] = 0
                stats["analyses_by_type"][analysis_type_str] += 1
                
                # Collect metrics
                if analysis.confidence_score is not None:
                    confidence_scores.append(analysis.confidence_score)
                
                if analysis.quality_score is not None:
                    quality_scores.append(analysis.quality_score)
                
                if analysis.execution_time_seconds is not None:
                    execution_times.append(analysis.execution_time_seconds)
                
                # Sum counters
                stats["total_files_processed"] += analysis.files_processed
                stats["total_tokens_used"] += analysis.tokens_used or 0
            
            # Calculate averages
            if confidence_scores:
                stats["average_confidence_score"] = sum(confidence_scores) / len(confidence_scores)
            
            if quality_scores:
                stats["average_quality_score"] = sum(quality_scores) / len(quality_scores)
            
            if execution_times:
                stats["average_execution_time"] = sum(execution_times) / len(execution_times)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {}
    
    async def search_analyses(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """Search analyses by name or description."""
        return await self.search(
            search_term,
            search_fields=["name", "description", "summary"],
            skip=skip,
            limit=limit
        )


# Global analysis service instance
analysis_service = AnalysisService()