"""
Base service class with common functionality for MongoDB, plus an in-memory fallback.
"""
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from beanie import Document
from bson import ObjectId
from ..models.base import BaseDocument
from ..core.logging import get_logger
from app.core.database import database as db_state  # runtime availability flag
import uuid

T = TypeVar('T', bound=BaseDocument)

logger = get_logger(__name__)


class InMemoryStore(Generic[T]):
    """Simple in-memory store mimicking subset of Beanie operations.

    A class-level registry ensures all services for the same model share the dataset.
    """

    _registry: dict[str, "InMemoryStore"] = {}

    def __init__(self, model: Type[T]):
        self.model = model
        self.items: dict[str, T] = {}

    @classmethod
    def for_model(cls, model: Type[T]):  # type: ignore
        key = model.__name__
        if key not in cls._registry:
            cls._registry[key] = cls(model)
        return cls._registry[key]

    async def create(self, **kwargs) -> T:  # type: ignore
        _id = kwargs.get("id") or str(uuid.uuid4())
        kwargs["id"] = _id
        instance = self.model(**kwargs)  # type: ignore
        self.items[_id] = instance
        return instance

    async def get(self, _id):  # type: ignore
        return self.items.get(str(_id))

    async def find(self, filter_criteria):  # type: ignore
        # Very naive filtering
        results = []
        for obj in self.items.values():
            match = True
            for k, v in filter_criteria.items():
                val = getattr(obj, k, None)
                if isinstance(v, dict) and "$regex" in v:
                    import re as _re
                    if not (isinstance(val, str) and _re.search(v["$regex"], val, _re.I)):
                        match = False
                        break
                elif val != v:
                    match = False
                    break
            if match:
                results.append(obj)
        return results

    async def count(self, filter_criteria):  # type: ignore
        return len(await self.find(filter_criteria))

    async def save(self, instance: T):  # type: ignore
        self.items[str(instance.id)] = instance

    async def delete(self, _id):  # type: ignore
        return self.items.pop(str(_id), None) is not None


def using_memory() -> bool:
    # Prefer explicit config flags if available
    try:
        from app.core.config import get_settings
        settings = get_settings()
        if settings.persistence_mode.lower() == "memory" or settings.disable_database:
            return True
    except Exception:
        pass
    return not db_state.available


class BaseService(Generic[T]):
    """Base service class with CRUD operations for MongoDB."""
    
    def __init__(self, model: Type[T]):
        self.model = model
    
    async def create(self, **kwargs) -> T:
        """Create a new instance."""
        try:
            if using_memory():
                # In-memory path
                store = InMemoryStore.for_model(self.model)
                instance = await store.create(**kwargs)  # type: ignore
            else:
                instance = self.model(**kwargs)
                await instance.save()
            logger.info(f"Created {self.model.__name__} with id: {instance.id}")
            return instance
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    async def get_by_id(self, id: ObjectId) -> Optional[T]:
        """Get instance by ID."""
        try:
            if using_memory():
                store = InMemoryStore.for_model(self.model)
                return await store.get(id)  # type: ignore
            return await self.model.get(id)
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            return None
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all instances with pagination and filtering."""
        try:
            # Build filter criteria
            filter_criteria = {}
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        filter_criteria[key] = {"$in": value}
                    else:
                        filter_criteria[key] = value
            
            # Create query with filters
            if using_memory():
                store = InMemoryStore.for_model(self.model)
                results = await store.find(filter_criteria)  # type: ignore
                # rudimentary skip/limit
                return results[skip: skip + limit]
            query = self.model.find(filter_criteria)
            
            # Apply sorting
            if sort_by:
                if sort_order.lower() == "desc":
                    query = query.sort(f"-{sort_by}")
                else:
                    query = query.sort(sort_by)
            else:
                # Default sorting by created_at desc
                query = query.sort("-created_at")
            
            return await query.skip(skip).limit(limit).to_list()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} list: {e}")
            return []
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count instances with optional filtering."""
        try:
            # Build filter criteria
            filter_criteria = {}
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        filter_criteria[key] = {"$in": value}
                    else:
                        filter_criteria[key] = value
            
            # Create query with filters and count
            if using_memory():
                store = InMemoryStore.for_model(self.model)
                return await store.count(filter_criteria)  # type: ignore
            return await self.model.find(filter_criteria).count()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0
    
    async def update(self, id: ObjectId, **kwargs) -> Optional[T]:
        """Update an instance."""
        try:
            instance = await self.get_by_id(id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            instance.update_timestamps()
            if using_memory():
                store = InMemoryStore.for_model(self.model)
                await store.save(instance)  # type: ignore
            else:
                await instance.save()
            logger.info(f"Updated {self.model.__name__} with id: {id}")
            return instance
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} id {id}: {e}")
            raise
    
    async def delete(self, id: ObjectId, soft_delete: bool = True) -> bool:
        """Delete an instance."""
        try:
            instance = await self.get_by_id(id)
            if not instance:
                return False
            
            if soft_delete and hasattr(instance, 'is_active'):
                await instance.soft_delete()
                logger.info(f"Soft deleted {self.model.__name__} with id: {id}")
            else:
                if using_memory():
                    store = InMemoryStore.for_model(self.model)
                    await store.delete(id)  # type: ignore
                else:
                    await instance.delete()
                logger.info(f"Hard deleted {self.model.__name__} with id: {id}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} id {id}: {e}")
            return False
    
    async def get_active(self, **kwargs) -> List[T]:
        """Get all active instances."""
        filters = kwargs.copy()
        filters['is_active'] = True
        return await self.get_all(filters=filters)
    
    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """Search instances by term in specified fields."""
        try:
            # Build MongoDB text search or regex search
            search_conditions = []
            for field in search_fields:
                search_conditions.append({field: {"$regex": search_term, "$options": "i"}})
            
            # Create query with search conditions
            filter_criteria = {"$or": search_conditions} if search_conditions else {}
            query = self.model.find(filter_criteria)
            
            return await query.skip(skip).limit(limit).to_list()
        except Exception as e:
            logger.error(f"Error searching {self.model.__name__}: {e}")
            return []


class ServiceException(Exception):
    """Base exception for service layer."""
    pass


class ValidationError(ServiceException):
    """Exception for validation errors."""
    pass


class NotFoundError(ServiceException):
    """Exception for resource not found errors."""
    pass


class ConflictError(ServiceException):
    """Exception for resource conflict errors."""
    pass