"""
FastAPI dependencies for the OpenSource Sensei application.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# from .database import get_db  # Commented out for MongoDB migration
from .security import security, get_current_user, User, api_key_manager


async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current active user from JWT token."""
    user = get_current_user(credentials)
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with admin privileges."""
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def verify_api_key(api_key: str) -> dict:
    """Verify API key and return key information."""
    key_info = api_key_manager.validate_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return key_info


# def get_db_session() -> Generator[Session, None, None]:
#     """Get database session dependency."""
#     yield from get_db()  # Commented out for MongoDB migration


class CommonQueryParams:
    """Common query parameters for pagination and filtering."""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ):
        self.skip = skip
        self.limit = min(limit, 1000)  # Maximum 1000 items per page
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "asc"


def common_parameters(
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
) -> CommonQueryParams:
    """Dependency for common query parameters."""
    return CommonQueryParams(skip, limit, sort_by, sort_order)


# Rate limiting dependency (simple in-memory implementation)
from collections import defaultdict
import time
from typing import Dict

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Check if request is allowed within rate limit."""
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True


rate_limiter = RateLimiter()


async def check_rate_limit(
    request_id: str,
    max_requests: int = 100,
    window_seconds: int = 3600
) -> bool:
    """Check rate limit for requests."""
    if not rate_limiter.is_allowed(request_id, max_requests, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return True


# File upload validation
def validate_file_size(max_size_mb: int = 100):
    """Dependency to validate file upload size."""
    def validator(content_length: int = 0):
        max_size_bytes = max_size_mb * 1024 * 1024
        if content_length > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_size_mb}MB"
            )
        return True
    return validator


# Health check dependencies
async def check_database_health() -> bool:
    """Check database health."""
    try:
        from .database import check_database_connection
        return await check_database_connection()
    except Exception:
        return False


async def check_redis_health() -> bool:
    """Check Redis health."""
    try:
        # This would check Redis connection in a real implementation
        return True
    except Exception:
        return False


# Background task dependencies
from typing import Any, Callable
import asyncio

class TaskManager:
    """Simple background task manager."""
    
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
    
    async def create_task(self, task_id: str, coro: Callable, *args, **kwargs) -> str:
        """Create a background task."""
        if task_id in self.tasks and not self.tasks[task_id].done():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Task already running"
            )
        
        task = asyncio.create_task(coro(*args, **kwargs))
        self.tasks[task_id] = task
        return task_id
    
    def get_task_status(self, task_id: str) -> dict:
        """Get task status."""
        if task_id not in self.tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task = self.tasks[task_id]
        if task.done():
            if task.exception():
                return {"status": "failed", "error": str(task.exception())}
            else:
                return {"status": "completed", "result": task.result()}
        else:
            return {"status": "running"}
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        return True


task_manager = TaskManager()


def get_task_manager() -> TaskManager:
    """Get task manager dependency."""
    return task_manager