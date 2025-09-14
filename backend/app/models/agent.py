"""
Agent document model for managing AI agents in MongoDB.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field
from enum import Enum

from .base import BaseDocument


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    SHUTTING_DOWN = "shutting_down"


class AgentType(str, Enum):
    """Agent type enumeration."""
    RESEARCH = "research"
    QA = "qa"
    CODE_REVIEW = "code_review"
    REPOSITORY_ANALYZER = "repository_analyzer"
    GENERIC = "generic"


class Agent(BaseDocument):
    """Agent document model for AI agent management."""
    
    # Basic information
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    agent_type: AgentType
    version: Optional[str] = Field(None, max_length=50)
    
    # Status
    status: AgentStatus = Field(default=AgentStatus.OFFLINE)
    last_seen_at: Optional[datetime] = None
    heartbeat_interval_seconds: int = Field(default=30, ge=1)
    
    # Configuration
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    capabilities: Optional[List[str]] = Field(default_factory=list)
    supported_tasks: Optional[List[str]] = Field(default_factory=list)
    
    # Performance metrics
    total_tasks_completed: int = Field(default=0, ge=0)
    total_tasks_failed: int = Field(default=0, ge=0)
    average_execution_time_seconds: Optional[float] = Field(None, ge=0.0)
    success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Resource usage
    cpu_usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_usage_mb: Optional[float] = Field(None, ge=0.0)
    disk_usage_mb: Optional[float] = Field(None, ge=0.0)
    
    # Current workload
    current_tasks: int = Field(default=0, ge=0)
    max_concurrent_tasks: int = Field(default=1, ge=1)
    
    # Error tracking
    last_error_message: Optional[str] = Field(None, max_length=2000)
    last_error_at: Optional[datetime] = None
    error_count: int = Field(default=0, ge=0)
    
    # Network information
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    endpoint_url: Optional[str] = Field(None, max_length=500)
    
    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list)
    environment: str = Field(default="development", max_length=50)
    
    class Settings:
        """Beanie document settings."""
        name = "agents"
        indexes = [
            "name",
            "agent_type",
            "status",
            "last_seen_at",
            "environment",
            "created_at"
        ]
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.agent_type}', status='{self.status}')>"
    
    async def add_capability(self, capability: str) -> None:
        """Add a capability to the agent."""
        if not self.capabilities:
            self.capabilities = []
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            await self.save()
    
    async def add_supported_task(self, task_type: str) -> None:
        """Add a supported task type."""
        if not self.supported_tasks:
            self.supported_tasks = []
        if task_type not in self.supported_tasks:
            self.supported_tasks.append(task_type)
            await self.save()
    
    async def add_tag(self, tag: str) -> None:
        """Add a tag to the agent."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
            await self.save()
    
    async def update_heartbeat(self) -> None:
        """Update agent heartbeat."""
        self.last_seen_at = datetime.utcnow()
        self.update_timestamps()
        await self.save()
    
    async def mark_online(self) -> None:
        """Mark agent as online."""
        self.status = AgentStatus.IDLE
        self.last_seen_at = datetime.utcnow()
        self.update_timestamps()
        await self.save()
    
    async def mark_offline(self) -> None:
        """Mark agent as offline."""
        self.status = AgentStatus.OFFLINE
        self.update_timestamps()
        await self.save()
    
    async def mark_busy(self) -> None:
        """Mark agent as busy."""
        self.status = AgentStatus.BUSY
        self.update_timestamps()
        await self.save()
    
    async def mark_idle(self) -> None:
        """Mark agent as idle."""
        if self.status == AgentStatus.BUSY:
            self.status = AgentStatus.IDLE
            self.update_timestamps()
            await self.save()
    
    async def mark_error(self, error_message: str) -> None:
        """Mark agent as in error state."""
        self.status = AgentStatus.ERROR
        self.last_error_message = error_message
        self.last_error_at = datetime.utcnow()
        self.error_count += 1
        self.update_timestamps()
        await self.save()
    
    async def update_performance_metrics(self, execution_time: float, success: bool) -> None:
        """Update agent performance metrics."""
        if success:
            self.total_tasks_completed += 1
        else:
            self.total_tasks_failed += 1
        
        # Update average execution time
        if self.total_tasks_completed > 0:
            current_avg = self.average_execution_time_seconds or 0
            self.average_execution_time_seconds = (
                (current_avg * (self.total_tasks_completed - 1) + execution_time) / self.total_tasks_completed
            )
        
        # Update success rate
        total_tasks = self.total_tasks_completed + self.total_tasks_failed
        if total_tasks > 0:
            self.success_rate = self.total_tasks_completed / total_tasks
        
        self.update_timestamps()
        await self.save()
    
    async def update_resource_usage(
        self,
        cpu_percent: Optional[float] = None,
        memory_mb: Optional[float] = None,
        disk_mb: Optional[float] = None
    ) -> None:
        """Update agent resource usage."""
        if cpu_percent is not None:
            self.cpu_usage_percent = cpu_percent
        if memory_mb is not None:
            self.memory_usage_mb = memory_mb
        if disk_mb is not None:
            self.disk_usage_mb = disk_mb
        
        self.update_timestamps()
        await self.save()
    
    def can_accept_task(self, task_type: str) -> bool:
        """Check if agent can accept a task of given type."""
        if self.status != AgentStatus.IDLE:
            return False
        
        if self.current_tasks >= self.max_concurrent_tasks:
            return False
        
        return task_type in (self.supported_tasks or [])
    
    async def increment_current_tasks(self) -> None:
        """Increment current task count."""
        self.current_tasks += 1
        if self.current_tasks >= self.max_concurrent_tasks:
            await self.mark_busy()
        else:
            await self.save()
    
    async def decrement_current_tasks(self) -> None:
        """Decrement current task count."""
        self.current_tasks = max(0, self.current_tasks - 1)
        if self.current_tasks < self.max_concurrent_tasks:
            await self.mark_idle()
        else:
            await self.save()
    
    @property
    def is_online(self) -> bool:
        """Check if agent is online."""
        return self.status not in [AgentStatus.OFFLINE, AgentStatus.SHUTTING_DOWN]
    
    @property
    def is_available(self) -> bool:
        """Check if agent is available for new tasks."""
        return self.status == AgentStatus.IDLE
    
    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy (not in error state and seen recently)."""
        if self.status == AgentStatus.ERROR:
            return False
        
        if not self.last_seen_at:
            return False
        
        # Consider healthy if seen within 2x heartbeat interval
        max_silence = self.heartbeat_interval_seconds * 2
        silence_duration = (datetime.utcnow() - self.last_seen_at).total_seconds()
        
        return silence_duration <= max_silence
    
    @property
    def workload_percentage(self) -> float:
        """Get current workload as percentage."""
        return (self.current_tasks / self.max_concurrent_tasks) * 100 if self.max_concurrent_tasks > 0 else 0.0