"""
FastAPI main application - simplified version.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
import sys
import os
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic settings class
class Settings:
    app_name: str = "OpenSource Sensei API"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    cors_origins: list = ["*"]
    persistence_mode: str = "memory"
    disable_database: bool = True

settings = Settings()

# Add project root to Python path to enable imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    
logger.info(f"Added project root to Python path: {project_root}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting OpenSource Sensei API...")
    logger.info("Running in memory mode (no database)")
    app.state.db_connected = False
    
    yield
    
    # Shutdown
    logger.info("Shutting down OpenSource Sensei API...")
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

# Include analysis endpoints if available
try:
    from app.api.endpoints.analysis import router as analysis_router
    app.include_router(analysis_router, prefix=f"{settings.api_prefix}", tags=["analysis"])
    logger.info("Analysis endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load analysis endpoints: {e}")
    logger.info("Running with basic endpoints only")


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
        return {
            "status": "healthy",
            "database": "disabled",
            "database_required": False,
            "persistence_mode": settings.persistence_mode,
            "version": settings.app_version,
            "environment": "development"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "database": "disabled", 
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