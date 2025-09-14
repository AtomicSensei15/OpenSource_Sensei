"""
API router aggregation.
"""
from fastapi import APIRouter
from ..core.config import get_settings  # type: ignore
from ..core.database import check_database_connection  # type: ignore
import logging
import asyncio
from .endpoints import projects, analyses, tasks, agents
from .dependencies import service_mode

# Main API router
api_router = APIRouter()

logger = logging.getLogger(__name__)

# Include all endpoint routers
api_router.include_router(projects.router)
api_router.include_router(analyses.router)
api_router.include_router(tasks.router)
api_router.include_router(agents.router)


@api_router.get("/health", tags=["system"], summary="API Health (prefixed)")
async def api_health():
	"""Health endpoint under the API prefix so frontend base URL works.

	Mirrors the root `/health` but is namespaced under the configured `api_prefix`.
	This prevents 404s when the frontend axios baseURL includes `/api/v1` and calls `/health`.
	"""
	settings = get_settings()
	db_healthy = False
	from app.core.config import get_settings as _gs
	_settings = _gs()
	memory_mode = _settings.persistence_mode == "memory" or _settings.disable_database
	try:
		# Attempt database check quickly with timeout to avoid hanging request
		try:
			db_healthy = await asyncio.wait_for(check_database_connection(), timeout=1.5)
		except Exception as e:  # noqa: BLE001
			logger.debug(f"Prefixed health DB check failed or timed out: {e}")
			db_healthy = False
		return {
			"status": "healthy",
			"database": ("connected" if db_healthy else "disconnected") if not memory_mode else "disabled",
			"database_required": not memory_mode,
			"persistence_mode": _settings.persistence_mode,
			"version": settings.app_version,
			"environment": "development" if settings.debug else "production",
			"prefixed": True,
		}
	except Exception as e:  # noqa: BLE001
		logger.error(f"Prefixed health check failed: {e}")
		return {
			"status": "degraded",
			"database": "disabled" if memory_mode else "disconnected",
			"error": str(e),
			"persistence_mode": _settings.persistence_mode,
			"version": settings.app_version,
			"prefixed": True,
		}


@api_router.get('/mode', tags=['system'], summary='Persistence mode')
async def persistence_mode():
    return {'mode': service_mode()}