"""
Project service for managing repository analysis projects.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import os
import tempfile
import shutil
from bson import ObjectId

from ..models.project import Project, ProjectStatus, ProjectType
from ..models.analysis import Analysis
from ..models.task import Task
from .base_service import BaseService, NotFoundError, ValidationError
from ..core.logging import get_logger
from ..core.config import get_settings

settings = get_settings()
logger = get_logger(__name__)


class ProjectService(BaseService[Project]):
    """Service for managing projects."""
    
    def __init__(self):
        super().__init__(Project)
    
    async def create_project(
        self,
        name: str,
        project_type: ProjectType,
        description: Optional[str] = None,
        source_url: Optional[str] = None,
        analysis_config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        try:
            # Validate project type and source
            if project_type == ProjectType.GITHUB_REPO and not source_url:
                raise ValidationError("GitHub repository URL is required")
            
            if project_type == ProjectType.LOCAL_REPO and not source_url:
                raise ValidationError("Local repository path is required")
            
            # Extract repository information for GitHub projects
            repository_name = None
            repository_owner = None
            
            if project_type == ProjectType.GITHUB_REPO and source_url:
                repo_info = self._parse_github_url(source_url)
                repository_name = repo_info.get('name')
                repository_owner = repo_info.get('owner')
            
            # Create project
            project = await self.create(
                name=name,
                description=description,
                project_type=project_type,
                source_url=source_url,
                repository_name=repository_name,
                repository_owner=repository_owner,
                analysis_config=analysis_config or {},
                user_id=user_id,
                status=ProjectStatus.CREATED
            )
            
            logger.info(f"Created project: {project.name} (ID: {project.id})")
            return project
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def start_analysis(self, project_id: str) -> Project:
        """Start analysis for a project."""
        project = await self.get_by_id(ObjectId(project_id))
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        if project.status != ProjectStatus.CREATED:
            raise ValidationError(f"Project is already {project.status}")
        
        try:
            # Update project status
            await project.mark_started()
            
            # Create storage directory
            storage_path = self._create_project_storage(project)
            project.source_path = storage_path
            await project.save()
            
            logger.info(f"Started analysis for project {project_id}")
            return project
            
        except Exception as e:
            logger.error(f"Error starting analysis for project {project_id}: {e}")
            await project.mark_failed(str(e))
            raise
    
    async def complete_analysis(
        self,
        project_id: str,
        results: Optional[Dict[str, Any]] = None
    ) -> Project:
        """Complete analysis for a project."""
        project = await self.get_by_id(ObjectId(project_id))
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        try:
            await project.mark_completed()
            
            # Update results if provided
            if results:
                if 'languages' in results:
                    project.languages_detected = results['languages']
                if 'technologies' in results:
                    project.technologies_detected = results['technologies']
                if 'total_files' in results:
                    project.total_files = results['total_files']
                if 'total_lines' in results:
                    project.total_lines = results['total_lines']
                if 'file_size_bytes' in results:
                    project.file_size_bytes = results['file_size_bytes']
            
            await project.save()
            logger.info(f"Completed analysis for project {project_id}")
            return project
            
        except Exception as e:
            logger.error(f"Error completing analysis for project {project_id}: {e}")
            raise
    
    async def fail_analysis(
        self,
        project_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Project:
        """Mark project analysis as failed."""
        project = await self.get_by_id(ObjectId(project_id))
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        try:
            await project.mark_failed(error_message, error_details)
            logger.error(f"Failed analysis for project {project_id}: {error_message}")
            return project
            
        except Exception as e:
            logger.error(f"Error marking project {project_id} as failed: {e}")
            raise
    
    async def update_progress(
        self,
        project_id: str,
        percentage: int,
        phase: Optional[str] = None
    ) -> Project:
        """Update project progress."""
        project = await self.get_by_id(ObjectId(project_id))
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        try:
            await project.update_progress(percentage, phase)
            return project
            
        except Exception as e:
            logger.error(f"Error updating progress for project {project_id}: {e}")
            raise
    
    async def get_project_analyses(self, project_id: str) -> List[Analysis]:
        """Get all analyses for a project."""
        project = await self.get_by_id(ObjectId(project_id))
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        # This would need to be implemented with a proper MongoDB query
        # Example: return await Analysis.find({"project_id": project.id}).to_list()
        return []
    
    async def get_project_tasks(self, project_id: str) -> List[Task]:
        """Get all tasks for a project."""
        project = await self.get_by_id(ObjectId(project_id))
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        # This would need to be implemented with a proper MongoDB query
        # Example: return await Task.find({"project_id": project.id}).to_list()
        return []
    
    async def get_projects_by_status(
        self,
        status: ProjectStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get projects by status."""
        return await self.get_all(skip=skip, limit=limit, filters={"status": status})
    
    async def get_projects_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get projects for a specific user."""
        return await self.get_all(skip=skip, limit=limit, filters={"user_id": user_id})
    
    async def search_projects(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Search projects by name or description."""
        return await self.search(
            search_term=search_term,
            search_fields=["name", "description", "repository_name", "repository_owner"],
            skip=skip,
            limit=limit
        )
    
    async def cleanup_old_projects(
        self,
        days_old: int = 30,
        dry_run: bool = False
    ) -> List[str]:
        """Clean up old completed projects."""
        # Find old completed projects
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Use MongoDB-specific query to find old projects
        projects = await self.model.find({
            "status": ProjectStatus.COMPLETED,
            "completed_at": {"$lt": cutoff_date}
        }).to_list()
        
        deleted_ids = []
        
        if not dry_run:
            for project in projects:
                await project.delete()
                deleted_ids.append(str(project.id))
        
        return deleted_ids
    
    def _parse_github_url(self, url: str) -> Dict[str, str]:
        """Parse GitHub URL to extract owner and repository name."""
        try:
            # Remove .git suffix if present
            url = url.rstrip('.git')
            
            # Handle different GitHub URL formats
            if url.startswith('https://github.com/'):
                parts = url.replace('https://github.com/', '').split('/')
            elif url.startswith('git@github.com:'):
                parts = url.replace('git@github.com:', '').split('/')
            else:
                # Try to extract from any URL format
                parts = url.split('/')[-2:]
            
            if len(parts) >= 2:
                return {
                    'owner': parts[-2],
                    'name': parts[-1]
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing GitHub URL {url}: {e}")
            return {}
    
    def _create_project_storage(self, project: Project) -> str:
        """Create storage directory for project."""
        try:
            storage_root = Path(settings.storage_path)
            storage_root.mkdir(parents=True, exist_ok=True)
            
            # Create project-specific directory
            project_dir = storage_root / f"project_{project.id}"
            project_dir.mkdir(exist_ok=True)
            
            return str(project_dir)
            
        except Exception as e:
            logger.error(f"Error creating storage for project {project.id}: {e}")
            raise


# Global project service instance
project_service = ProjectService()