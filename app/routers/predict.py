"""Prediction endpoints — validation and orchestration only."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.transaction_repo import TransactionRepository
from app.dependencies import (
    get_alert_service,
    get_db,
    get_explanation_service,
    get_performance_tracker,
    get_transaction_repo,
    require_prediction_service,
)
from app.errors import persistence_error_detail
from app.models.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionWithExplanation,
    TransactionInput,
    TransactionRecord,
)
from app.modules.auth.dependencies import require_client_auth
from app.monitoring.performance_tracker import PerformanceTracker
from app.services.alert_service import AlertService
from app.services.explanation_service import ExplanationService
from app.services.prediction_service import PredictionService
from app.utils.cold_start import is_demo_cold_start

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Predictions"],
    dependencies=[Depends(require_client_auth)],
)


def _cold_start(transaction: TransactionInput) -> bool:
    """Demo cold-start heuristic (no stable account identifiers in payloads)."""
    return is_demo_cold_start(transaction)


@router.post(
    "",
    response_model=PredictionWithExplanation,
    summary="Score a transaction",
)
async def predict_one(
    transaction: TransactionInput,
    prediction_service: Annotated[
        PredictionService, Depends(require_prediction_service)
    ],
    explanation_service: Annotated[
        ExplanationService, Depends(get_explanation_service)
    ],
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
    transaction_repo: Annotated[
        TransactionRepository, Depends(get_transaction_repo)
    ],
    performance_tracker: Annotated[
        PerformanceTracker, Depends(get_performance_tracker)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PredictionWithExplanation:
    is_cold = _cold_start(transaction)
    result = await asyncio.to_thread(
        prediction_service.predict,
        transaction,
        is_cold,
    )
    explanation = await asyncio.to_thread(
        explanation_service.explain,
        result,
        transaction,
    )

    try:
        await transaction_repo.save_prediction(
            db,
            result,
            explanation,
            time_offset=float(transaction.time),
        )
    except IntegrityError:
        logger.warning("Duplicate prediction for %s", transaction.transaction_id)
        raise HTTPException(
            status_code=409,
            detail={
                "message": "A prediction for this transaction_id already exists.",
                "transaction_id": transaction.transaction_id,
            },
        ) from None
    except Exception as exc:
        logger.exception("Prediction persistence degraded: %s", exc)
        detail = persistence_error_detail(exc)
        detail["message"] = (
            "Prediction succeeded but persisting the audit log failed. "
            "Downstream systems may be missing this row."
        )
        raise HTTPException(status_code=503, detail=detail) from None

    performance_tracker.record(result)
    if result.decision != "APPROVED":
        await alert_service.broadcast_alert(result, explanation)

    return PredictionWithExplanation(
        **result.model_dump(),
        explanation=explanation,
    )


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    summary="Batch score up to 100 transactions",
)
async def predict_batch(
    body: BatchPredictionRequest,
    prediction_service: Annotated[
        PredictionService, Depends(require_prediction_service)
    ],
    explanation_service: Annotated[
        ExplanationService, Depends(get_explanation_service)
    ],
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
    transaction_repo: Annotated[
        TransactionRepository, Depends(get_transaction_repo)
    ],
    performance_tracker: Annotated[
        PerformanceTracker, Depends(get_performance_tracker)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BatchPredictionResponse:
    t0 = time.perf_counter()
    tasks = [
        asyncio.to_thread(
            prediction_service.predict,
            tx,
            _cold_start(tx),
        )
        for tx in body.transactions
    ]
    results = await asyncio.gather(*tasks)
    explain_tasks = [
        asyncio.to_thread(explanation_service.explain, r, tx)
        for r, tx in zip(results, body.transactions, strict=True)
    ]
    explanations = await asyncio.gather(*explain_tasks)

    out: list[PredictionWithExplanation] = []
    skipped_duplicates = 0
    for r, ex, tx in zip(results, explanations, body.transactions, strict=True):
        try:
            await transaction_repo.save_prediction(
                db, r, ex, time_offset=float(tx.time)
            )
        except IntegrityError:
            skipped_duplicates += 1
            logger.warning(
                "Batch row skipped duplicate transaction_id=%s", r.transaction_id
            )
            continue
        except Exception as exc:
            logger.exception("Batch persistence error: %s", exc)
            detail = persistence_error_detail(exc)
            detail["message"] = "Batch ingest aborted due to database error."
            raise HTTPException(status_code=503, detail=detail) from None
        performance_tracker.record(r)
        if r.decision != "APPROVED":
            await alert_service.broadcast_alert(r, ex)
        out.append(PredictionWithExplanation(**r.model_dump(), explanation=ex))

    blocked = sum(1 for x in results if x.decision == "BLOCKED")
    review = sum(1 for x in results if x.decision == "REVIEW")
    approved = sum(1 for x in results if x.decision == "APPROVED")

    elapsed = (time.perf_counter() - t0) * 1000
    return BatchPredictionResponse(
        results=out,
        total=len(body.transactions),
        skipped_duplicates=skipped_duplicates,
        blocked_count=blocked,
        review_count=review,
        approved_count=approved,
        processing_time_ms=float(elapsed),
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionRecord,
    summary="Retrieve a persisted prediction",
)
async def get_prediction(
    transaction_id: str,
    transaction_repo: Annotated[
        TransactionRepository, Depends(get_transaction_repo)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionRecord:
    row = await transaction_repo.get_by_transaction_id(db, transaction_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "Unknown transaction_id", "transaction_id": transaction_id},
        )
    return TransactionRecord(
        transaction_id=row.transaction_id,
        amount=float(row.amount),
        fraud_probability=float(row.fraud_probability),
        decision=row.decision,
        model_used=row.model_used,
        is_cold_start=bool(row.is_cold_start),
        explanation=row.explanation or "",
        predicted_at=row.predicted_at,
    )
