"""
Base document model with common fields and functionality for MongoDB.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from beanie import Document
from pydantic import Field
import uuid
from bson import ObjectId


class BaseDocument(Document):
    """Base document model with common fields."""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    class Settings:
        """Beanie document settings."""
        use_state_management = True
        validate_on_save = True
    
    def update_timestamps(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    async def update_from_dict(self, data: Dict[str, Any]) -> 'BaseDocument':
        """Update document from dictionary."""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', '_id']:
                setattr(self, key, value)
        self.update_timestamps()
        await self.save()
        return self
    
    async def soft_delete(self) -> 'BaseDocument':
        """Soft delete the document."""
        self.is_active = False
        self.update_timestamps()
        await self.save()
        return self
    
    async def hard_delete(self) -> None:
        """Permanently delete the document."""
        await self.delete()
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Convert document to dictionary."""
        data = super().dict(**kwargs)
        # Convert ObjectId to string for JSON serialization
        if '_id' in data:
            data['id'] = str(data.pop('_id'))
        return data
    
    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())