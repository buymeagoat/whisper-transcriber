"""Health check routes for the Whisper Transcriber API."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import redis.asyncio as redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from api.orm_bootstrap import engine
from api.services.redis_cache import get_cache_service
from api.settings import settings

router = APIRouter(prefix="/health", tags=["health"])


@dataclass
class CheckResult:
    """Result of an individual health check."""

    healthy: bool
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"healthy": self.healthy, **self.details}


async def _check_database() -> CheckResult:
    """Verify the application can communicate with the database."""

    def ping_db() -> Tuple[bool, Dict[str, Any]]:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True, {"message": "Database connection successful"}
        except SQLAlchemyError as exc:  # pragma: no cover - defensive guard
            return False, {"error": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive guard
            return False, {"error": str(exc)}

    healthy, details = await asyncio.to_thread(ping_db)
    return CheckResult(healthy=healthy, details=details)


async def _check_redis() -> CheckResult:
    """Verify the Redis cache is reachable."""

    redis_url = os.getenv("REDIS_URL", settings.redis_url)

    try:
        cache_service = await get_cache_service()
        if cache_service and cache_service.redis_pool:
            await cache_service.redis_pool.ping()
            return CheckResult(True, {"message": "Redis cache reachable", "source": "cache_service"})

        client = redis.from_url(redis_url)
        try:
            await client.ping()
            return CheckResult(True, {"message": "Redis cache reachable", "source": "direct"})
        finally:
            await client.close()
    except Exception as exc:  # pragma: no cover - defensive guard
        return CheckResult(False, {"error": str(exc), "redis_url": redis_url})


def _check_models() -> CheckResult:
    """Validate that Whisper models can be loaded or downloaded."""

    models_dir = settings.models_dir
    preloaded = []
    for model_name in settings.available_models:
        candidate = models_dir / f"{model_name}.pt"
        if candidate.exists():
            preloaded.append(model_name)

    details: Dict[str, Any] = {
        "models_dir": str(models_dir),
        "preloaded_models": preloaded,
        "default_model": settings.default_model,
    }

    try:
        import whisper  # type: ignore

        details["whisper_version"] = getattr(whisper, "__version__", "unknown")
        details["download_required"] = settings.default_model not in preloaded
        return CheckResult(True, details)
    except Exception as exc:  # pragma: no cover - defensive guard
        details["error"] = str(exc)
        return CheckResult(False, details)


@router.get("/livez")
async def livez() -> JSONResponse:
    """Liveness probe – confirms the service is running."""

    return JSONResponse({"status": "ok", "message": "Service is running"})


@router.get("/readyz")
async def readyz() -> JSONResponse:
    """Readiness probe with dependency checks."""

    db_result, redis_result = await asyncio.gather(_check_database(), _check_redis())
    model_result = _check_models()

    healthy = all([db_result.healthy, redis_result.healthy, model_result.healthy])
    status_code = 200 if healthy else 503

    payload = {
        "status": "ready" if healthy else "degraded",
        "checks": {
            "database": db_result.to_dict(),
            "redis": redis_result.to_dict(),
            "models": model_result.to_dict(),
        },
    }

    return JSONResponse(status_code=status_code, content=payload)
