"""WebSocket broadcasting for flagged transactions."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime, timezone

from fastapi import WebSocket

from app.models.schemas import PredictionResult

logger = logging.getLogger(__name__)


class AlertService:
    """Push fraud/review alerts to connected dashboards."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self.alert_history: deque[dict] = deque(maxlen=100)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        await websocket.send_json(
            {
                "type": "history",
                "payload": list(self.alert_history),
            }
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_alert(self, result: PredictionResult, explanation: str) -> None:
        if result.decision not in ("BLOCKED", "REVIEW"):
            return
        ts = datetime.now(timezone.utc).isoformat()
        top_signal = ""
        if result.top_shap_features:
            top_signal = result.top_shap_features[0].feature_name

        alert_payload = {
            "type": "alert",
            "transaction_id": result.transaction_id,
            "amount": result.amount,
            "fraud_probability": result.fraud_probability,
            "decision": result.decision,
            "top_risk_signal": top_signal,
            "explanation": explanation,
            "model_used": result.model_used,
            "timestamp": ts,
        }
        self.alert_history.append(alert_payload)

        async def _send(ws: WebSocket) -> None:
            try:
                await ws.send_json(alert_payload)
            except Exception as e:
                logger.debug("WebSocket send failed; disconnecting client: %s", e)
                self.disconnect(ws)

        if self.active_connections:
            await asyncio.gather(*(_send(ws) for ws in list(self.active_connections)))

    async def send_heartbeat(self) -> None:
        utcnow = datetime.now(timezone.utc).isoformat()
        msg = {"type": "heartbeat", "timestamp": utcnow}

        async def _send(ws: WebSocket) -> None:
            try:
                await ws.send_json(msg)
            except Exception:
                self.disconnect(ws)

        if self.active_connections:
            await asyncio.gather(*(_send(ws) for ws in list(self.active_connections)))
