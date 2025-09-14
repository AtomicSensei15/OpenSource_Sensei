"""
MongoDB database configuration and connection management.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional, List, Type, Any
from beanie import Document
import logging
import os
from urllib.parse import urlparse
import re

from .config import get_settings

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager."""
    client: Optional[AsyncIOMotorClient] = None
    database: Any = None
    available: bool = False

# Global database instance
database = Database()

def _extract_or_build_db_name(uri: str, explicit_name: str) -> str:
    """Derive a database name from explicit setting or URI path.

    Rules:
    1. If explicit_name provided (default setting) use it.
    2. Else if URI path has a segment (mongodb://host:port/mydb) use that.
    3. Sanitize: remove illegal chars (Mongo forbids /\"$*<>:|? and starting with 'system.').
    4. Replace dots with underscores to avoid '.' error.
    5. Fallback to 'opensourcesensei'.
    """
    if explicit_name:
        candidate = explicit_name
    else:
        parsed = urlparse(uri)
        path = parsed.path.lstrip('/') if parsed.path else ''
        candidate = path or 'opensourcesensei'
    # Replace illegal characters; keep alphanumerics, dash, underscore
    candidate = re.sub(r"[^A-Za-z0-9_-]", "_", candidate)
    # Mongo error we saw was due to '.' so ensure none remain
    candidate = candidate.replace('.', '_')
    # Prevent empty
    if not candidate:
        candidate = 'opensourcesensei'
    return candidate


async def connect_to_mongo():
    """Initialize MongoDB connection and Beanie ODM with validation and graceful fallback."""
    settings = get_settings()
    mongodb_uri = os.getenv("MONGODB_URI", settings.mongodb_uri)
    explicit_name = os.getenv("MONGODB_DATABASE", settings.mongodb_database)

    try:
        db_name = _extract_or_build_db_name(mongodb_uri, explicit_name)
        if explicit_name and explicit_name != db_name:
            logger.warning(
                f"Adjusted provided database name '{explicit_name}' to sanitized '{db_name}' for MongoDB compliance"
            )

        database.client = AsyncIOMotorClient(mongodb_uri)
        database.database = database.client.get_database(db_name)

        # Test connection quick ping
        await database.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB (db='{db_name}')")
        database.available = True

        # Import models here to avoid circular imports
        from ..models.project import Project  # noqa: WPS433
        from ..models.analysis import Analysis  # noqa: WPS433
        from ..models.task import Task  # noqa: WPS433
        from ..models.agent import Agent  # noqa: WPS433

        models: List[Type[Document]] = [Project, Analysis, Task, Agent]

        await init_beanie(database=database.database, document_models=models)
        logger.info("Beanie ODM initialized successfully")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to connect to MongoDB, continuing without DB: {e}")
        # Null out to reflect no DB connection
        database.client = None
        database.database = None
        database.available = False

async def close_mongo_connection():
    """Close MongoDB connection."""
    try:
        if database.client:
            database.client.close()
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")

def get_database():
    """Get database instance."""
    if database.database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database.database

async def check_database_connection():
    """Check if MongoDB connection is working."""
    try:
        if database.client:
            await database.client.admin.command('ping')
            logger.info("MongoDB connection successful")
            return True
        else:
            logger.error("MongoDB client not initialized")
            return False
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        return False