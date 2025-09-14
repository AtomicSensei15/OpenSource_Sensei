"""
Analysis document model for storing analysis results in MongoDB.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field
from enum import Enum
from bson import ObjectId

from .base import BaseDocument


class AnalysisType(str, Enum):
    """Analysis type enumeration."""
    CODE_REVIEW = "code_review"
    QA_GENERATION = "qa_generation"
    RESEARCH = "research"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    STRUCTURE_ANALYSIS = "structure_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    DOCUMENTATION_ANALYSIS = "documentation_analysis"


class AnalysisStatus(str, Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Analysis(BaseDocument):
    """Analysis document model for storing analysis results."""
    
    # Basic information
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    analysis_type: AnalysisType
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING)
    
    # Relationships
    project_id: ObjectId = Field(...)
    
    # Agent information
    agent_id: Optional[str] = Field(None, max_length=100)
    agent_type: Optional[str] = Field(None, max_length=50)
    
    # Analysis configuration
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Results
    results: Optional[Dict[str, Any]] = Field(default_factory=dict)
    summary: Optional[str] = Field(None, max_length=5000)
    recommendations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Progress tracking
    progress_percentage: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = Field(None, max_length=100)
    total_steps: Optional[int] = Field(None, ge=0)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error handling
    error_message: Optional[str] = Field(None, max_length=2000)
    error_details: Optional[Dict[str, Any]] = None
    
    # Resource usage
    execution_time_seconds: Optional[float] = Field(None, ge=0.0)
    memory_usage_mb: Optional[float] = Field(None, ge=0.0)
    tokens_used: Optional[int] = Field(None, ge=0)  # For AI model usage
    
    # File processing
    files_processed: int = Field(default=0, ge=0)
    files_total: Optional[int] = Field(None, ge=0)
    files_skipped: int = Field(default=0, ge=0)
    
    # Output files
    output_files: Optional[List[str]] = Field(default_factory=list)
    
    class Settings:
        """Beanie document settings."""
        name = "analyses"
        indexes = [
            "name",
            "analysis_type",
            "status",
            "project_id",
            "agent_id",
            "created_at"
        ]
    
    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, type='{self.analysis_type}', status='{self.status}')>"
    
    async def add_output_file(self, file_path: str) -> None:
        """Add an output file."""
        if not self.output_files:
            self.output_files = []
        if file_path not in self.output_files:
            self.output_files.append(file_path)
            await self.save()
    
    async def update_progress(self, percentage: int, step: Optional[str] = None) -> None:
        """Update analysis progress."""
        self.progress_percentage = max(0, min(100, percentage))
        if step:
            self.current_step = step
        self.update_timestamps()
        await self.save()
    
    async def mark_started(self, agent_id: Optional[str] = None) -> None:
        """Mark analysis as started."""
        self.status = AnalysisStatus.RUNNING
        self.started_at = datetime.utcnow()
        if agent_id:
            self.agent_id = agent_id
        self.update_timestamps()
        await self.save()
    
    async def mark_completed(self, execution_time: Optional[float] = None) -> None:
        """Mark analysis as completed."""
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
        
        if execution_time:
            self.execution_time_seconds = execution_time
        elif self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.update_timestamps()
        await self.save()
    
    async def mark_failed(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.error_details = error_details
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.update_timestamps()
        await self.save()
    
    async def mark_cancelled(self) -> None:
        """Mark analysis as cancelled."""
        self.status = AnalysisStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.update_timestamps()
        await self.save()
    
    @property
    def is_completed(self) -> bool:
        """Check if analysis is completed."""
        return self.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]
    
    @property
    def is_running(self) -> bool:
        """Check if analysis is running."""
        return self.status == AnalysisStatus.RUNNING
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get analysis duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def success_rate(self) -> Optional[float]:
        """Calculate success rate based on files processed."""
        if not self.files_total or self.files_total == 0:
            return None
        
        return self.files_processed / self.files_total