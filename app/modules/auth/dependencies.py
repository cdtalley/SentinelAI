"""FastAPI dependencies for client authentication."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings
from app.dependencies import get_settings_sync

logger = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)


def _parse_api_keys(raw: str) -> frozenset[str]:
    return frozenset(
        part.strip() for part in raw.split(",") if part.strip()
    )


def _extract_api_key(
    request: Request,
    bearer_credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    header_key = request.headers.get("X-API-Key")
    if header_key:
        return header_key.strip()
    if bearer_credentials and bearer_credentials.scheme.lower() == "bearer":
        return bearer_credentials.credentials.strip()
    return None


async def require_client_auth(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_sync)],
    bearer_credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ],
) -> str | None:
    """
    Require credentials when AUTH_MODE=api_key; otherwise no-op.

    Returns the validated key string (or a placeholder) for observability hooks.
    """
    if settings.AUTH_MODE == "none":
        return None

    keys = _parse_api_keys(settings.API_KEYS)
    if not keys:
        logger.error("AUTH_MODE=api_key but API_KEYS is empty — refusing traffic.")
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Server misconfiguration: API key auth enabled without keys.",
            },
        )

    token = _extract_api_key(request, bearer_credentials)
    if not token or token not in keys:
        raise HTTPException(
            status_code=401,
            detail={
                "message": (
                    "Authentication required. "
                    "Send X-API-Key or Authorization: Bearer <key>."
                ),
            },
        )
    return token


def verify_ws_api_key(websocket: WebSocket, settings: Settings) -> str | None:
    """Validate WebSocket connection before accept (query ?api_key= or X-API-Key header)."""
    if settings.AUTH_MODE == "none":
        return None
    keys = _parse_api_keys(settings.API_KEYS)
    if not keys:
        raise HTTPException(status_code=503, detail={"message": "API_KEYS not configured."})

    token = websocket.query_params.get("api_key") or websocket.headers.get("x-api-key")
    if not token or token.strip() not in keys:
        # WebSocket cannot return JSON 401 after accept; reject during handshake
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid or missing api_key for WebSocket."},
        )
    return token.strip()


