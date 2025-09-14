"""
FastAPI main application with MongoDB integration.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
import sys
from pathlib import Path

"""Adjust Python path so absolute 'app.*' imports work whether launched as 'python backend/main.py'
or 'uvicorn backend.main:app'."""
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir  # backend/
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.core.config import get_settings  # type: ignore  # noqa: E402
from app.core.database import connect_to_mongo, close_mongo_connection, check_database_connection  # type: ignore  # noqa: E402
from app.core.logging import setup_logging  # type: ignore  # noqa: E402
from app.api.router import api_router  # type: ignore  # noqa: E402


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting OpenSource Sensei API...")
    # Log persistence configuration early for diagnostics
    logger.info(
        "Persistence configuration: mode=%s disable_database=%s (set PERSISTENCE_MODE=memory to force in-memory)",
        settings.persistence_mode,
        settings.disable_database,
    )
    # Decide whether to attempt DB connection
    # Normalize again defensively (in case settings loaded before validator in some edge path)
    pmode = (settings.persistence_mode or "database").strip().lower()
    skip_db = pmode == "memory" or settings.disable_database
    logger.debug("Evaluated skip_db=%s (persistence_mode=%s disable_database=%s)", skip_db, pmode, settings.disable_database)
    if skip_db:
        logger.info("Database connection skipped (in-memory mode enabled)")
        app.state.db_connected = False
    else:
        try:
            await connect_to_mongo()
            logger.info("Database connection established")
            app.state.db_connected = True
        except Exception as e:
            logger.warning(f"Failed to connect to database: {e}")
            logger.warning("Continuing without database (fallback to in-memory store)")
            app.state.db_connected = False
    
    yield
    
    # Shutdown
    logger.info("Shutting down OpenSource Sensei API...")
    if getattr(app.state, 'db_connected', False):
        await close_mongo_connection()
        logger.info("Database connection closed")
    else:
        logger.info("No database connection to close")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered open source project analysis and enhancement platform",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include API router
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "OpenSource Sensei API",
        "version": settings.app_version,
        "status": "running",
        "persistence_mode": settings.persistence_mode,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db_healthy = False
        if getattr(app.state, 'db_connected', False):
            db_healthy = await check_database_connection()
        
        return {
            "status": "healthy",  # Service is healthy even without DB for development
            "database": ("connected" if db_healthy else "disconnected") if not settings.disable_database and settings.persistence_mode != "memory" else "disabled",
            "database_required": not (settings.persistence_mode == "memory" or settings.disable_database),
            "persistence_mode": settings.persistence_mode,
            "version": settings.app_version,
            "environment": "development"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "database": "disconnected", 
            "error": str(e),
            "version": settings.app_version
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )