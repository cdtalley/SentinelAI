"""Health, readiness, and operational metrics."""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db,
    get_performance_tracker,
    get_settings_sync,
    peek_is_model_ready,
    peek_model_loader,
    peek_ollama_client,
)
from app.limiter import limiter
from app.models.schemas import HealthResponse, PerformanceMetrics
from app.config import Settings
from app.modules.auth.dependencies import require_client_auth
from app.monitoring.performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


async def _probe_dependencies(
    settings: Settings,
    db: AsyncSession,
    performance_tracker: PerformanceTracker,
) -> tuple[bool, bool, bool, HealthResponse]:
    loader = peek_model_loader()
    model_loaded = peek_is_model_ready() and loader is not None and loader.is_ready()

    client = peek_ollama_client()
    ollama_ok = False
    if client is not None:
        try:
            chk = await asyncio.to_thread(client.health_check)
            ollama_ok = bool(chk.get("available", False))
        except Exception:
            logger.debug("Ollama health probe failed.", exc_info=True)

    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        logger.debug("Database readiness probe failed.", exc_info=True)

    status = "degraded" if not db_connected or not model_loaded else "ok"
    body = HealthResponse(
        status=status,
        model_loaded=model_loaded,
        model_version=settings.MODEL_VERSION,
        ollama_available=bool(ollama_ok),
        db_connected=db_connected,
        total_predictions_served=performance_tracker.get_total_served(),
        uptime_seconds=performance_tracker.get_uptime_seconds(),
    )
    return model_loaded, db_connected, ollama_ok, body


@router.get("/health/live")
@limiter.exempt
async def health_live() -> dict[str, str]:
    """Liveness: process is up (orchestrators should not restart on DB blips)."""
    return {"status": "ok"}


@router.get("/health/ready")
@limiter.exempt
async def health_ready(
    settings: Annotated[Settings, Depends(get_settings_sync)],
    performance_tracker: Annotated[
        PerformanceTracker, Depends(get_performance_tracker)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Readiness: DB + models required for scoring traffic."""
    model_loaded, db_connected, _, body = await _probe_dependencies(
        settings, db, performance_tracker
    )
    if not (model_loaded and db_connected):
        return JSONResponse(
            status_code=503,
            content=body.model_dump(mode="json"),
        )
    return JSONResponse(status_code=200, content=body.model_dump(mode="json"))


@router.get("/health", response_model=HealthResponse)
@limiter.exempt
async def health(
    settings: Annotated[Settings, Depends(get_settings_sync)],
    performance_tracker: Annotated[
        PerformanceTracker, Depends(get_performance_tracker)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HealthResponse:
    """Full status payload (HTTP 200; use ``/health/ready`` for success gating)."""
    _ml, _dbc, _oo, body = await _probe_dependencies(settings, db, performance_tracker)
    return body


@router.get(
    "/metrics",
    response_model=PerformanceMetrics,
    dependencies=[Depends(require_client_auth)],
)
async def global_metrics(
    performance_tracker: Annotated[
        PerformanceTracker, Depends(get_performance_tracker)
    ],
) -> PerformanceMetrics:
    """Rolling KPIs — gated when API key auth is enabled."""
    return performance_tracker.get_metrics()
