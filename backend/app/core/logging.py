"""
Logging configuration for the OpenSource Sensei application.
"""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from .config import get_settings

settings = get_settings()


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    
    # Create logs directory if it doesn't exist
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "default",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "celery": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "openai": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }
    
    # Add file handler if log file is specified
    if settings.log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "filename": settings.log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            if "file" not in logger_config["handlers"]:
                logger_config["handlers"].append("file")
    
    return config


def setup_logging():
    """Setup logging configuration."""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.log_level}")
    if settings.log_file:
        logger.info(f"Log file: {settings.log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


# Custom log filters
class HealthCheckFilter(logging.Filter):
    """Filter to exclude health check requests from logs."""
    
    def filter(self, record):
        return "/health" not in getattr(record, "message", "")


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from logs."""
    
    SENSITIVE_FIELDS = ["password", "token", "key", "secret", "authorization"]
    
    def filter(self, record):
        if hasattr(record, "msg"):
            msg = str(record.msg)
            for field in self.SENSITIVE_FIELDS:
                if field.lower() in msg.lower():
                    record.msg = msg.replace(field, "***REDACTED***")
        return True


# Exception logging decorator
def log_exceptions(logger: logging.Logger | None = None):
    """Decorator to log exceptions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.exception(f"Exception in {func.__name__}: {e}")
                raise
        return wrapper
    return decorator


# Performance logging decorator
def log_performance(logger: logging.Logger | None = None, log_args: bool = False):
    """Decorator to log function performance."""
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                log_msg = f"{func.__name__} executed in {execution_time:.4f}s"
                if log_args and args:
                    log_msg += f" with args: {args[:3]}..."  # Log first 3 args only
                
                log.info(log_msg)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log.error(f"{func.__name__} failed after {execution_time:.4f}s: {e}")
                raise
        return wrapper
    return decorator