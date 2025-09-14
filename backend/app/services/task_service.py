"""
Task service for managing background tasks.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from ..models.task import Task, TaskStatus, TaskPriority
from ..models.project import Project
from ..models.analysis import Analysis
from ..models.agent import Agent
from .base_service import BaseService, NotFoundError, ValidationError
from ..core.logging import get_logger

logger = get_logger(__name__)


class TaskService(BaseService[Task]):
    """Service for managing tasks."""
    
    def __init__(self):
        super().__init__(Task)
    
    async def create_task(
        self,
        name: str,
        task_type: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        project_id: Optional[ObjectId] = None,
        analysis_id: Optional[ObjectId] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 60,
        scheduled_at: Optional[datetime] = None
    ) -> Task:
        """Create a new task."""
        try:
            # Validate relationships
            if project_id:
                project = await Project.get(project_id)
                if not project:
                    raise NotFoundError(f"Project {project_id} not found")
            
            if analysis_id:
                analysis = await Analysis.get(analysis_id)
                if not analysis:
                    raise NotFoundError(f"Analysis {analysis_id} not found")
            
            # Create task
            task = await self.create(
                name=name,
                description=description,
                task_type=task_type,
                priority=priority,
                project_id=project_id,
                analysis_id=analysis_id,
                config=config or {},
                input_data=input_data or {},
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                scheduled_at=scheduled_at or datetime.utcnow(),
                status=TaskStatus.PENDING
            )
            
            logger.info(f"Created task: {task.name} (ID: {task.id})")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise
    
    async def start_task(
        self,
        task_id: ObjectId,
        agent_id: Optional[str] = None
    ) -> Task:
        """Start a task."""
        task = await self.get_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        
        if task.status not in [TaskStatus.PENDING, TaskStatus.RETRYING]:
            raise ValidationError(f"Task is in status {task.status}, cannot start")
        
        try:
            await task.mark_started(agent_id)
            logger.info(f"Started task {task_id}" + (f" with agent {agent_id}" if agent_id else ""))
            return task
            
        except Exception as e:
            logger.error(f"Error starting task {task_id}: {e}")
            raise
    
    async def complete_task(
        self,
        task_id: ObjectId,
        output_data: Optional[Dict[str, Any]] = None,
        result_summary: Optional[str] = None
    ) -> Task:
        """Complete a task."""
        task = await self.get_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        
        try:
            if result_summary:
                task.result_summary = result_summary
            
            await task.mark_completed(output_data)
            logger.info(f"Completed task {task_id}")
            return task
            
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            raise
    
    async def fail_task(
        self,
        task_id: ObjectId,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> Task:
        """Mark task as failed and optionally retry."""
        task = await self.get_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        
        try:
            await task.mark_failed(error_message, error_details)
            
            # Check if task should be retried
            if retry and task.can_retry:
                await task.mark_for_retry()
                logger.info(f"Task {task_id} failed, scheduled for retry ({task.retry_count}/{task.max_retries})")
            else:
                logger.error(f"Task {task_id} failed permanently: {error_message}")
            
            return task
            
        except Exception as e:
            logger.error(f"Error failing task {task_id}: {e}")
            raise

    async def cancel_task(self, task_id: ObjectId) -> Task:
        """Cancel a task."""
        task = await self.get_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        
        if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING]:
            raise ValidationError(f"Cannot cancel task in status {task.status}")
        
        try:
            await task.mark_cancelled()
            logger.info(f"Cancelled task {task_id}")
            return task
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            raise
    
    async def update_progress(
        self,
        task_id: ObjectId,
        percentage: int,
        step: Optional[str] = None
    ) -> Task:
        """Update task progress."""
        task = await self.get_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        
        try:
            await task.update_progress(percentage, step)
            return task
            
        except Exception as e:
            logger.error(f"Error updating progress for task {task_id}: {e}")
            raise
    
    async def get_pending_tasks(
        self,
        task_type: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        limit: int = 100
    ) -> List[Task]:
        """Get pending tasks ordered by priority and scheduled time."""
        try:
            filters: Dict[str, Any] = {"status": TaskStatus.PENDING}
            
            if task_type:
                filters["task_type"] = task_type
            
            if priority:
                filters["priority"] = priority
            
            # Get tasks ordered by priority (high to low) then by scheduled time (old to new)
            tasks = await self.get_all(
                limit=limit,
                filters=filters,
                sort_by="scheduled_at",
                sort_order="asc"
            )
            
            # Sort by priority value (higher is better)
            tasks.sort(key=lambda t: (t.priority_value, t.scheduled_at or datetime.min), reverse=True)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []
    
    async def get_running_tasks(self, agent_id: Optional[str] = None) -> List[Task]:
        """Get running tasks, optionally filtered by agent."""
        try:
            filters: Dict[str, Any] = {"status": TaskStatus.RUNNING}
            
            if agent_id:
                filters["agent_id"] = agent_id
            
            return await self.get_all(filters=filters)
            
        except Exception as e:
            logger.error(f"Error getting running tasks: {e}")
            return []
    
    async def get_tasks_for_retry(self) -> List[Task]:
        """Get tasks that are ready for retry."""
        try:
            # Tasks in RETRYING status that are scheduled for now or earlier
            tasks = await self.get_all(filters={"status": TaskStatus.RETRYING})
            
            # Filter by scheduled time
            ready_tasks = []
            now = datetime.utcnow()
            
            for task in tasks:
                if task.scheduled_at and task.scheduled_at <= now:
                    ready_tasks.append(task)
            
            return ready_tasks
            
        except Exception as e:
            logger.error(f"Error getting tasks for retry: {e}")
            return []
    
    async def get_tasks_by_project(
        self,
        project_id: ObjectId,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks for a specific project."""
        return await self.get_all(skip=skip, limit=limit, filters={"project_id": project_id})
    
    async def get_tasks_by_analysis(
        self,
        analysis_id: ObjectId,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks for a specific analysis."""
        return await self.get_all(skip=skip, limit=limit, filters={"analysis_id": analysis_id})
    
    async def get_tasks_by_agent(
        self,
        agent_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks assigned to a specific agent."""
        return await self.get_all(skip=skip, limit=limit, filters={"agent_id": agent_id})
    
    async def get_task_statistics(self, task_id: ObjectId) -> Dict[str, Any]:
        """Get task statistics."""
        task = await self.get_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        
        try:
            stats = {
                "task_id": task.id,
                "name": task.name,
                "type": task.task_type,
                "status": task.status,
                "priority": task.priority,
                "progress_percentage": task.progress_percentage,
                "current_step": task.current_step,
                "total_steps": task.total_steps,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "execution_time_seconds": task.execution_time_seconds,
                "memory_usage_mb": task.memory_usage_mb,
                "cpu_usage_percent": task.cpu_usage_percent,
                "scheduled_at": task.scheduled_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "duration_seconds": task.duration_seconds,
                "is_completed": task.is_completed,
                "is_running": task.is_running,
                "is_ready": task.is_ready,
                "can_retry": task.can_retry
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics for task {task_id}: {e}")
            return {}
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide task statistics."""
        try:
            all_tasks = await self.get_all()
            
            stats = {
                "total_tasks": len(all_tasks),
                "pending_tasks": 0,
                "running_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "cancelled_tasks": 0,
                "retrying_tasks": 0,
                "tasks_by_type": {},
                "tasks_by_priority": {
                    "low": 0,
                    "normal": 0,
                    "high": 0,
                    "critical": 0
                },
                "average_execution_time": 0.0,
                "total_retry_count": 0
            }
            
            execution_times = []
            
            for task in all_tasks:
                # Count by status
                if task.status == TaskStatus.PENDING:
                    stats["pending_tasks"] += 1
                elif task.status == TaskStatus.RUNNING:
                    stats["running_tasks"] += 1
                elif task.status == TaskStatus.COMPLETED:
                    stats["completed_tasks"] += 1
                elif task.status == TaskStatus.FAILED:
                    stats["failed_tasks"] += 1
                elif task.status == TaskStatus.CANCELLED:
                    stats["cancelled_tasks"] += 1
                elif task.status == TaskStatus.RETRYING:
                    stats["retrying_tasks"] += 1
                
                # Count by type
                if task.task_type not in stats["tasks_by_type"]:
                    stats["tasks_by_type"][task.task_type] = 0
                stats["tasks_by_type"][task.task_type] += 1
                
                # Count by priority
                if hasattr(task.priority, 'value'):
                    priority_key = task.priority.value
                    if priority_key in stats["tasks_by_priority"]:
                        stats["tasks_by_priority"][priority_key] += 1
                
                # Collect metrics
                if task.execution_time_seconds is not None:
                    execution_times.append(task.execution_time_seconds)
                
                # Sum retry counts
                stats["total_retry_count"] += task.retry_count
            
            # Calculate averages
            if execution_times:
                stats["average_execution_time"] = sum(execution_times) / len(execution_times)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {}
    
    async def cleanup_old_tasks(
        self,
        days_old: int = 7,
        keep_failed: bool = True
    ) -> List[ObjectId]:
        """Clean up old completed tasks."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old tasks to clean up
            old_tasks = []
            all_tasks = await self.get_all()
            
            for task in all_tasks:
                if task.completed_at and task.completed_at < cutoff_date:
                    # Keep failed tasks if requested
                    if keep_failed and task.status == TaskStatus.FAILED:
                        continue
                    
                    # Only clean up completed, failed, or cancelled tasks
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                        old_tasks.append(task)
            
            # Delete old tasks
            task_ids = []
            for task in old_tasks:
                await self.delete(task.id, soft_delete=False)
                task_ids.append(task.id)
            
            if task_ids:
                logger.info(f"Cleaned up {len(task_ids)} old tasks")
            
            return task_ids
            
        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {e}")
            return []
    
    async def search_tasks(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Search tasks by name or description."""
        return await self.search(
            search_term,
            search_fields=["name", "description", "result_summary"],
            skip=skip,
            limit=limit
        )


# Global task service instance
task_service = TaskService()