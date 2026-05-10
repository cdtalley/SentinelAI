"""History, analytics, drift — read-mostly routers."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.transaction_repo import TransactionRepository
from app.dependencies import (
    get_db,
    get_drift_detector,
    get_performance_tracker,
    get_settings_sync,
    get_transaction_repo,
)
from app.models.schemas import DriftReport, PerformanceMetrics, TransactionRecord
from app.modules.auth.dependencies import require_client_auth
from app.monitoring.drift_detector import DriftDetector
from app.monitoring.performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Transactions"],
    dependencies=[Depends(require_client_auth)],
)


def _aggregate_shap(samples: list[list[dict]]) -> dict[str, list[float]]:
    acc: defaultdict[str, list[float]] = defaultdict(list)
    for row in samples:
        for feat in row:
            if not isinstance(feat, dict):
                continue
            name = feat.get("feature_name")
            if not name:
                continue
            sv = feat.get("abs_impact")
            if sv is None:
                sv = abs(float(feat.get("shap_value", 0.0)))
            acc[str(name)].append(float(sv))
    return dict(acc)


class BaselineResponse(BaseModel):
    """Acknowledge drift baseline establishment."""

    message: str
    feature_keys: list[str]


@router.get("", response_model=list[TransactionRecord])
async def list_transactions(
    db: Annotated[AsyncSession, Depends(get_db)],
    transaction_repo: Annotated[
        TransactionRepository, Depends(get_transaction_repo)
    ],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    decision: Annotated[
        str | None,
        Query(description="Optional filter APPROVED|REVIEW|BLOCKED"),
    ] = None,
) -> list[TransactionRecord]:
    if decision not in (None, "APPROVED", "REVIEW", "BLOCKED"):
        raise HTTPException(
            status_code=422,
            detail={"message": "decision must be APPROVED, REVIEW, or BLOCKED."},
        )
    rows = await transaction_repo.list_recent(
        db, limit=limit, decision_filter=decision
    )
    return [
        TransactionRecord(
            transaction_id=r.transaction_id,
            amount=float(r.amount),
            fraud_probability=float(r.fraud_probability),
            decision=r.decision,
            model_used=r.model_used,
            is_cold_start=bool(r.is_cold_start),
            explanation=r.explanation or "",
            predicted_at=r.predicted_at,
        )
        for r in rows
    ]


@router.get("/metrics", response_model=PerformanceMetrics)
async def transaction_metrics_window(
    performance_tracker: Annotated[
        PerformanceTracker, Depends(get_performance_tracker)
    ],
) -> PerformanceMetrics:
    return performance_tracker.get_metrics()


@router.get("/drift", response_model=DriftReport)
async def drift_snapshot(
    settings: Annotated[Settings, Depends(get_settings_sync)],
    drift_detector: Annotated[DriftDetector, Depends(get_drift_detector)],
    transaction_repo: Annotated[
        TransactionRepository, Depends(get_transaction_repo)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DriftReport:
    window = settings.DRIFT_CHECK_WINDOW
    samples = await transaction_repo.get_feature_sample(db, window=window)
    feature_data = _aggregate_shap(samples)
    report = drift_detector.check_drift(
        feature_data, window_size=settings.DRIFT_CHECK_WINDOW
    )
    return report


@router.post("/drift/baseline", response_model=BaselineResponse)
async def establish_drift_baseline(
    settings: Annotated[Settings, Depends(get_settings_sync)],
    drift_detector: Annotated[DriftDetector, Depends(get_drift_detector)],
    transaction_repo: Annotated[
        TransactionRepository, Depends(get_transaction_repo)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaselineResponse:
    """Capture PSI reference distribution using persisted SHAP impacts."""
    window = settings.DRIFT_CHECK_WINDOW
    samples = await transaction_repo.get_feature_sample(db, window=window)
    feature_data = _aggregate_shap(samples)
    if not feature_data:
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Insufficient SHAP history to baseline — ingest live predictions first."
                ),
            },
        )
    drift_detector.set_baseline(feature_data)
    return BaselineResponse(
        message="Drift PSI baseline refreshed from persisted transactions.",
        feature_keys=sorted(feature_data.keys()),
    )
