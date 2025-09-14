"""
Project document model for storing repository analysis projects in MongoDB.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field
from enum import Enum

from .base import BaseDocument


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    CREATED = "created"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectType(str, Enum):
    """Project type enumeration."""
    GITHUB_REPO = "github_repo"
    LOCAL_REPO = "local_repo"
    ARCHIVE_FILE = "archive_file"
    SINGLE_FILE = "single_file"


class Project(BaseDocument):
    """Project document model for repository analysis."""
    
    # Basic project information
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    project_type: ProjectType
    status: ProjectStatus = Field(default=ProjectStatus.CREATED)
    
    # Source information
    source_url: Optional[str] = Field(None, max_length=1000)  # GitHub URL, file path, etc.
    source_path: Optional[str] = Field(None, max_length=1000)  # Local storage path
    repository_name: Optional[str] = Field(None, max_length=255)
    repository_owner: Optional[str] = Field(None, max_length=255)
    branch: str = Field(default="main", max_length=255)
    
    # Analysis configuration
    analysis_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    include_patterns: Optional[List[str]] = Field(default_factory=list)
    exclude_patterns: Optional[List[str]] = Field(default_factory=list)
    
    # Analysis results summary
    total_files: int = Field(default=0, ge=0)
    total_lines: int = Field(default=0, ge=0)
    languages_detected: Optional[Dict[str, Any]] = Field(default_factory=dict)
    technologies_detected: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Progress tracking
    progress_percentage: int = Field(default=0, ge=0, le=100)
    current_phase: Optional[str] = Field(None, max_length=100)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error handling
    error_message: Optional[str] = Field(None, max_length=2000)
    error_details: Optional[Dict[str, Any]] = None
    
    # Metadata
    file_size_bytes: Optional[int] = Field(None, ge=0)
    archive_type: Optional[str] = Field(None, max_length=50)  # zip, tar.gz, etc.
    
    # User tracking (for future multi-user support)
    user_id: Optional[str] = Field(None, max_length=100)
    
    class Settings:
        """Beanie document settings."""
        name = "projects"
        indexes = [
            "name",
            "status", 
            "repository_name",
            "repository_owner",
            "user_id",
            "created_at"
        ]
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    async def update_progress(self, percentage: int, phase: Optional[str] = None) -> None:
        """Update project progress."""
        self.progress_percentage = max(0, min(100, percentage))
        if phase:
            self.current_phase = phase
        self.update_timestamps()
        await self.save()
    
    async def mark_started(self) -> None:
        """Mark project as started."""
        self.status = ProjectStatus.ANALYZING
        self.started_at = datetime.utcnow()
        self.update_timestamps()
        await self.save()
    
    async def mark_completed(self) -> None:
        """Mark project as completed."""
        self.status = ProjectStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
        self.current_phase = "completed"
        self.update_timestamps()
        await self.save()
    
    async def mark_failed(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark project as failed."""
        self.status = ProjectStatus.FAILED
        self.error_message = error_message
        self.error_details = error_details
        self.completed_at = datetime.utcnow()
        self.update_timestamps()
        await self.save()
    
    async def mark_cancelled(self) -> None:
        """Mark project as cancelled."""
        self.status = ProjectStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.update_timestamps()
        await self.save()
    
    @property
    def is_completed(self) -> bool:
        """Check if project is completed (success or failure)."""
        return self.status in [ProjectStatus.COMPLETED, ProjectStatus.FAILED, ProjectStatus.CANCELLED]
    
    @property
    def is_analyzing(self) -> bool:
        """Check if project is actively being processed."""
        return self.status == ProjectStatus.ANALYZING
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Get project duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())