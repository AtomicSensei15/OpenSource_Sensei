"""
Pydantic schemas for API request/response models.
"""
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Generic types for pagination
T = TypeVar('T')

# Base schemas
class BaseResponse(BaseModel):
    """Base response schema with common fields."""
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


# Pagination
class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    data: List[T]
    total: int
    skip: int
    limit: int


# Project schemas
class ProjectStatus(str, Enum):
    CREATED = "created"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectType(str, Enum):
    GITHUB_REPO = "github_repo"
    LOCAL_REPO = "local_repo"
    ARCHIVE_FILE = "archive_file"
    SINGLE_FILE = "single_file"


class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: ProjectType
    source_url: Optional[str] = None
    analysis_config: Optional[Dict[str, Any]] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    branch: str = "main"


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    analysis_config: Optional[Dict[str, Any]] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


class ProjectResponse(BaseResponse):
    """Schema for project response."""
    name: str
    description: Optional[str]
    project_type: ProjectType
    status: ProjectStatus
    source_url: Optional[str]
    source_path: Optional[str]
    repository_name: Optional[str]
    repository_owner: Optional[str]
    branch: Optional[str]
    analysis_config: Optional[Dict[str, Any]]
    include_patterns: Optional[List[str]]
    exclude_patterns: Optional[List[str]]
    total_files: int = 0
    total_lines: int = 0
    languages_detected: Optional[Dict[str, Any]]
    technologies_detected: Optional[Dict[str, Any]]
    progress_percentage: int = 0
    current_phase: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    file_size_bytes: Optional[int]
    user_id: Optional[str]


# Analysis schemas
class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisCreate(BaseModel):
    """Schema for creating an analysis."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    analysis_type: str = Field(..., min_length=1, max_length=50)
    config: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None


class AnalysisUpdate(BaseModel):
    """Schema for updating an analysis."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseResponse):
    """Schema for analysis response."""
    name: str
    description: Optional[str]
    analysis_type: str
    status: AnalysisStatus
    project_id: str
    agent_id: Optional[str]
    agent_type: Optional[str]
    config: Optional[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    summary: Optional[str]
    recommendations: Optional[List[Dict[str, Any]]]
    confidence_score: Optional[float]
    quality_score: Optional[float]
    progress_percentage: int = 0
    current_step: Optional[str]
    total_steps: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    execution_time_seconds: Optional[float]
    files_processed: int = 0
    files_total: Optional[int]
    files_skipped: int = 0
    output_files: Optional[List[str]]


# Task schemas
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCreate(BaseModel):
    """Schema for creating a task."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: str = Field(..., min_length=1, max_length=100)
    priority: TaskPriority = TaskPriority.NORMAL
    config: Optional[Dict[str, Any]] = None
    input_data: Optional[Dict[str, Any]] = None
    max_retries: int = Field(3, ge=0, le=10)
    retry_delay_seconds: int = Field(60, ge=0)
    scheduled_at: Optional[datetime] = None
    depends_on_task_ids: Optional[List[int]] = None
    tags: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    config: Optional[Dict[str, Any]] = None
    input_data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class TaskResponse(BaseResponse):
    """Schema for task response."""
    name: str
    description: Optional[str]
    task_type: str
    status: TaskStatus
    priority: TaskPriority
    project_id: Optional[str]
    analysis_id: Optional[str]
    agent_id: Optional[str]
    agent_type: Optional[str]
    config: Optional[Dict[str, Any]]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    result_summary: Optional[str]
    progress_percentage: int = 0
    current_step: Optional[str]
    total_steps: Optional[int]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    max_retries: int = 3
    retry_count: int = 0
    retry_delay_seconds: int = 60
    error_message: Optional[str]
    execution_time_seconds: Optional[float]
    depends_on_task_ids: Optional[List[str]]
    blocks_task_ids: Optional[List[str]]
    tags: Optional[List[str]]


# Agent schemas
class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    SHUTTING_DOWN = "shutting_down"


class AgentType(str, Enum):
    RESEARCH = "research"
    QA = "qa"
    CODE_REVIEW = "code_review"
    REPOSITORY_ANALYZER = "repository_analyzer"
    GENERIC = "generic"


class AgentCreate(BaseModel):
    """Schema for creating an agent."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    agent_type: AgentType
    version: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    supported_tasks: Optional[List[str]] = None
    max_concurrent_tasks: int = Field(1, ge=1, le=10)
    heartbeat_interval_seconds: int = Field(30, ge=5, le=300)
    host: Optional[str] = None
    port: Optional[int] = None
    environment: str = "development"
    tags: Optional[List[str]] = None


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    supported_tasks: Optional[List[str]] = None
    max_concurrent_tasks: Optional[int] = Field(None, ge=1, le=10)
    heartbeat_interval_seconds: Optional[int] = Field(None, ge=5, le=300)
    host: Optional[str] = None
    port: Optional[int] = None
    environment: Optional[str] = None
    tags: Optional[List[str]] = None


class AgentResponse(BaseResponse):
    """Schema for agent response."""
    name: str
    description: Optional[str]
    agent_type: AgentType
    version: Optional[str]
    status: AgentStatus
    last_seen_at: Optional[datetime]
    heartbeat_interval_seconds: int = 30
    config: Optional[Dict[str, Any]]
    capabilities: Optional[List[str]]
    supported_tasks: Optional[List[str]]
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    average_execution_time_seconds: Optional[float]
    success_rate: Optional[float]
    cpu_usage_percent: Optional[float]
    memory_usage_mb: Optional[float]
    disk_usage_mb: Optional[float]
    current_tasks: int = 0
    max_concurrent_tasks: int = 1
    last_error_message: Optional[str]
    last_error_at: Optional[datetime]
    error_count: int = 0
    host: Optional[str]
    port: Optional[int]
    endpoint_url: Optional[str]
    tags: Optional[List[str]]
    environment: Optional[str]


# Common response schemas
class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None
    success: bool = False


# Statistics schemas
class ProjectStatistics(BaseModel):
    """Schema for project statistics."""
    total_projects: int
    active_projects: int
    completed_projects: int
    failed_projects: int
    projects_by_type: Dict[str, int]
    projects_by_status: Dict[str, int]
    average_completion_time_hours: float
    total_files_analyzed: int
    total_lines_analyzed: int


class AnalysisStatistics(BaseModel):
    """Schema for analysis statistics."""
    total_analyses: int
    pending_analyses: int
    running_analyses: int
    completed_analyses: int
    failed_analyses: int
    analyses_by_type: Dict[str, int]
    average_confidence_score: float
    average_quality_score: float
    average_execution_time: float
    total_files_processed: int
    total_tokens_used: int


class TaskStatistics(BaseModel):
    """Schema for task statistics."""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    tasks_by_type: Dict[str, int]
    tasks_by_priority: Dict[str, int]
    average_execution_time: float
    total_retry_count: int


class AgentStatistics(BaseModel):
    """Schema for agent statistics."""
    total_agents: int
    online_agents: int
    idle_agents: int
    busy_agents: int
    error_agents: int
    offline_agents: int
    agents_by_type: Dict[str, int]
    total_tasks_completed: int
    total_tasks_failed: int
    average_success_rate: float


class SystemStatistics(BaseModel):
    """Schema for system-wide statistics."""
    projects: ProjectStatistics
    analyses: AnalysisStatistics
    tasks: TaskStatistics
    agents: AgentStatistics
    uptime_seconds: float
    version: str