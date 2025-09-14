"""
Task document model for background task management in MongoDB.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field
from enum import Enum
from bson import ObjectId

from .base import BaseDocument


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseDocument):
    """Task document model for background task management."""
    
    # Basic information
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    task_type: str = Field(..., max_length=100)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    
    # Relationships
    project_id: Optional[ObjectId] = None
    analysis_id: Optional[ObjectId] = None
    
    # Agent information
    agent_id: Optional[str] = Field(None, max_length=100)
    agent_type: Optional[str] = Field(None, max_length=50)
    
    # Task configuration
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Results
    output_data: Optional[Dict[str, Any]] = None
    result_summary: Optional[str] = Field(None, max_length=2000)
    
    # Progress tracking
    progress_percentage: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = Field(None, max_length=100)
    total_steps: Optional[int] = Field(None, ge=0)
    
    # Timing
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Retry logic
    max_retries: int = Field(default=3, ge=0)
    retry_count: int = Field(default=0, ge=0)
    retry_delay_seconds: int = Field(default=60, ge=0)
    
    # Error handling
    error_message: Optional[str] = Field(None, max_length=2000)
    error_details: Optional[Dict[str, Any]] = None
    last_error_at: Optional[datetime] = None
    
    # Resource usage
    execution_time_seconds: Optional[float] = Field(None, ge=0.0)
    memory_usage_mb: Optional[float] = Field(None, ge=0.0)
    cpu_usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    # Dependencies
    depends_on_task_ids: Optional[List[ObjectId]] = Field(default_factory=list)
    blocks_task_ids: Optional[List[ObjectId]] = Field(default_factory=list)
    
    # Metadata
    task_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    
    class Settings:
        """Beanie document settings."""
        name = "tasks"
        indexes = [
            "name",
            "task_type",
            "status",
            "priority",
            "project_id",
            "analysis_id",
            "agent_id",
            "scheduled_at",
            "created_at"
        ]
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    async def add_dependency(self, task_id: ObjectId) -> None:
        """Add a task dependency."""
        if not self.depends_on_task_ids:
            self.depends_on_task_ids = []
        if task_id not in self.depends_on_task_ids:
            self.depends_on_task_ids.append(task_id)
            await self.save()
    
    async def add_blocked_task(self, task_id: ObjectId) -> None:
        """Add a task that's blocked by this task."""
        if not self.blocks_task_ids:
            self.blocks_task_ids = []
        if task_id not in self.blocks_task_ids:
            self.blocks_task_ids.append(task_id)
            await self.save()
    
    async def add_tag(self, tag: str) -> None:
        """Add a tag to the task."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
            await self.save()
    
    async def update_progress(self, percentage: int, step: Optional[str] = None) -> None:
        """Update task progress."""
        self.progress_percentage = max(0, min(100, percentage))
        if step:
            self.current_step = step
        self.update_timestamps()
        await self.save()
    
    async def mark_started(self, agent_id: Optional[str] = None) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        if agent_id:
            self.agent_id = agent_id
        self.update_timestamps()
        await self.save()
    
    async def mark_completed(self, output_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
        
        if output_data:
            self.output_data = output_data
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.update_timestamps()
        await self.save()
    
    async def mark_failed(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.error_details = error_details
        self.last_error_at = datetime.utcnow()
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.update_timestamps()
        await self.save()
    
    async def mark_cancelled(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.update_timestamps()
        await self.save()
    
    async def mark_for_retry(self) -> None:
        """Mark task for retry."""
        if self.can_retry:
            self.status = TaskStatus.RETRYING
            self.retry_count += 1
            self.scheduled_at = datetime.utcnow()
            self.update_timestamps()
            await self.save()
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    @property
    def is_running(self) -> bool:
        """Check if task is running."""
        return self.status == TaskStatus.RUNNING
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready to run (no pending dependencies)."""
        return self.status == TaskStatus.PENDING
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def priority_value(self) -> int:
        """Get numeric priority value for sorting."""
        priority_map = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.CRITICAL: 4
        }
        return priority_map.get(self.priority, 2)