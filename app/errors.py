"""Centralized HTTP error detail helpers (no stack traces in production by default)."""

from __future__ import annotations

from typing import Any

from app.config import get_settings


def persistence_error_detail(exc: Exception) -> dict[str, Any]:
    """503 payload for database failures — technical detail only when safe."""
    settings = get_settings()
    detail: dict[str, Any] = {
        "message": "Database operation failed.",
        "error": type(exc).__name__,
    }
    if settings.EXPOSE_ERROR_DETAILS or settings.APP_ENV == "development":
        detail["technical"] = str(exc)
    return detail
