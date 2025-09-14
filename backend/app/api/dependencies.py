"""
Service factory and dependency injection.
"""
from typing import Callable, Dict, Type, TypeVar, cast
from fastapi import Depends

from ..models.project import Project
from ..models.analysis import Analysis
from ..models.task import Task
from ..models.agent import Agent
from ..services.project_service import ProjectService
from ..services.analysis_service import AnalysisService
from ..services.task_service import TaskService
from ..services.agent_service import AgentService

# Type variable for services
T = TypeVar('T')

# Service instances
_services: Dict[Type, object] = {}

def service_mode() -> str:
    """Return current persistence mode for diagnostics (mongo or memory)."""
    try:
        from ..core.database import database as db_state
        return "mongo" if db_state.available else "memory"
    except Exception:  # pragma: no cover
        return "unknown"

# Get a service instance with dependency injection
def get_service(service_class: Type[T]) -> T:
    """Get or create a service instance."""
    if service_class not in _services:
        _services[service_class] = service_class()
    return cast(T, _services[service_class])

# Service dependencies
def get_project_service() -> ProjectService:
    """Dependency for ProjectService."""
    return get_service(ProjectService)

def get_analysis_service() -> AnalysisService:
    """Dependency for AnalysisService."""
    return get_service(AnalysisService)

def get_task_service() -> TaskService:
    """Dependency for TaskService."""
    return get_service(TaskService)

def get_agent_service() -> AgentService:
    """Dependency for AgentService."""
    return get_service(AgentService)