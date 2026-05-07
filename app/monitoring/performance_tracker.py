"""In-memory sliding-window operational metrics."""

from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timezone

from app.models.schemas import PerformanceMetrics, PredictionResult


class PerformanceTracker:
    """Rolling window KPIs mirrored to HTTP health and dashboards."""

    def __init__(self, window_size: int = 1000, model_version: str = "unknown") -> None:
        self._window: deque = deque(maxlen=window_size)
        self._window_size_target = window_size
        self._model_version = model_version
        self._start_time: float = time.time()
        self._total_served: int = 0

    def set_model_version(self, version: str) -> None:
        self._model_version = version

    def record(self, result: PredictionResult) -> None:
        ts = result.predicted_at.isoformat()
        self._window.append(
            {
                "fraud_probability": float(result.fraud_probability),
                "decision": result.decision,
                "processing_time_ms": float(result.processing_time_ms),
                "predicted_at": ts,
            }
        )
        self._total_served += 1

    def get_metrics(self) -> PerformanceMetrics:
        preds = list(self._window)
        n = len(preds)
        if n == 0:
            return PerformanceMetrics(
                window_size=0,
                total_predictions=0,
                blocked_count=0,
                review_count=0,
                approved_count=0,
                fraud_rate_estimate=0.0,
                avg_fraud_probability=0.0,
                avg_processing_time_ms=0.0,
                model_version=self._model_version,
                computed_at=datetime.now(timezone.utc),
            )
        blk = sum(1 for x in preds if x["decision"] == "BLOCKED")
        rev = sum(1 for x in preds if x["decision"] == "REVIEW")
        app = sum(1 for x in preds if x["decision"] == "APPROVED")
        fps = sum(x["fraud_probability"] for x in preds) / n
        ms = sum(x["processing_time_ms"] for x in preds) / n
        fraud_rate_estimate = blk / n if n else 0.0

        return PerformanceMetrics(
            window_size=n,
            total_predictions=n,
            blocked_count=blk,
            review_count=rev,
            approved_count=app,
            fraud_rate_estimate=float(fraud_rate_estimate),
            avg_fraud_probability=float(fps),
            avg_processing_time_ms=float(ms),
            model_version=self._model_version,
            computed_at=datetime.now(timezone.utc),
        )

    def get_uptime_seconds(self) -> float:
        return float(time.time() - self._start_time)

    def get_total_served(self) -> int:
        return int(self._total_served)
