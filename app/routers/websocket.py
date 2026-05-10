"""Real-time fraud alert WebSocket."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.dependencies import require_alert_service_sync
from app.modules.auth.dependencies import verify_ws_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Alerts"])


@router.websocket("/alerts")
async def alerts_channel(websocket: WebSocket) -> None:
    """Push BLOCKED / REVIEW alerts instantly; emits periodic heartbeats."""
    settings = get_settings()
    verify_ws_api_key(websocket, settings)
    alert_service = require_alert_service_sync()
    await alert_service.connect(websocket)

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(float(settings.WEBSOCKET_HEARTBEAT_SECONDS))
            await alert_service.send_heartbeat()

    hb = asyncio.create_task(heartbeat())
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    except Exception as exc:
        logger.debug("WebSocket loop ended: %s", exc)
    finally:
        hb.cancel()
        try:
            await hb
        except asyncio.CancelledError:
            pass
        alert_service.disconnect(websocket)
