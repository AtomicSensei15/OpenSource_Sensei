"""Database / document models package."""
"""
Database models for OpenSource Sensei backend.
"""
from .base import BaseDocument
from .project import Project, ProjectStatus, ProjectType
from .analysis import Analysis, AnalysisType, AnalysisStatus
from .task import Task, TaskStatus, TaskPriority
from .agent import Agent, AgentStatus, AgentType

# Ensure all models are registered with Beanie
__all__ = [
    # Base classes
    "BaseDocument",
    
    # Project models
    "Project",
    "ProjectStatus", 
    "ProjectType",
    
    # Analysis models
    "Analysis",
    "AnalysisType",
    "AnalysisStatus",
    
    # Task models  
    "Task",
    "TaskStatus",
    "TaskPriority",
    
    # Agent models
    "Agent",
    "AgentStatus", 
    "AgentType",
]