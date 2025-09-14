"""Core utilities package."""
"""
Core module for OpenSource Sensei backend application.
"""
from .config import get_settings, Settings
from .database import get_database, connect_to_mongo, close_mongo_connection, check_database_connection
from .logging import setup_logging, get_logger
from .security import (
    create_access_token,
    verify_token,
    get_current_user,
    generate_api_key,
    validate_api_key,
    sanitize_input,
    validate_file_upload
)
from .dependencies import (
    get_current_active_user,
    get_current_admin_user,
    # get_db_session,  # Commented out for MongoDB migration
    common_parameters,
    check_rate_limit,
    task_manager
)

__all__ = [
    # Config
    "get_settings",
    "Settings",
    
    # Database
    "get_database",
    "connect_to_mongo", 
    "close_mongo_connection",
    "check_database_connection",
    
    # Logging
    "setup_logging",
    "get_logger",
    
    # Security
    "create_access_token",
    "verify_token",
    "get_current_user",
    "generate_api_key",
    "validate_api_key",
    "sanitize_input",
    "validate_file_upload",
    
    # Dependencies
    "get_current_active_user",
    "get_current_admin_user", 
    # "get_db_session",  # Commented out for MongoDB migration
    "common_parameters",
    "check_rate_limit",
    "task_manager"
]