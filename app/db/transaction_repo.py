"""Persistence access for predictions — no business rules."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import TransactionLog
from app.models.schemas import PredictionResult


class TransactionRepository:
    """CRUD-ish helpers for prediction logging."""

    async def save_prediction(
        self,
        db: AsyncSession,
        result: PredictionResult,
        explanation: str,
        time_offset: float | None = None,
    ) -> None:
        shap_serializable = [
            {
                "feature_name": s.feature_name,
                "shap_value": s.shap_value,
                "direction": s.direction,
                "abs_impact": s.abs_impact,
            }
            for s in result.top_shap_features
        ]
        row = TransactionLog(
            id=uuid.uuid4(),
            transaction_id=result.transaction_id,
            amount=result.amount,
            time_offset=time_offset,
            fraud_probability=result.fraud_probability,
            decision=result.decision,
            model_used=result.model_used,
            model_version=result.model_version,
            is_cold_start=result.is_cold_start,
            top_shap_features=shap_serializable,
            explanation=explanation or None,
            processing_time_ms=result.processing_time_ms,
            predicted_at=result.predicted_at,
        )
        db.add(row)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise

    async def get_by_transaction_id(
        self, db: AsyncSession, transaction_id: str
    ) -> TransactionLog | None:
        stmt = select(TransactionLog).where(
            TransactionLog.transaction_id == transaction_id
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_recent(
        self,
        db: AsyncSession,
        limit: int = 100,
        decision_filter: str | None = None,
    ) -> list[TransactionLog]:
        stmt = select(TransactionLog).order_by(TransactionLog.predicted_at.desc())
        if decision_filter:
            stmt = stmt.where(TransactionLog.decision == decision_filter)
        stmt = stmt.limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_performance_window(self, db: AsyncSession, window: int = 1000) -> dict:
        id_stmt = (
            select(TransactionLog.id)
            .order_by(TransactionLog.predicted_at.desc())
            .limit(window)
        )
        id_res = await db.execute(id_stmt)
        ids = list(id_res.scalars().all())
        if not ids:
            return {
                "window": window,
                "count": 0,
                "avg_fraud_probability": 0.0,
                "avg_processing_time_ms": 0.0,
                "decisions": {"APPROVED": 0, "REVIEW": 0, "BLOCKED": 0},
            }

        stmt = select(
            func.count(TransactionLog.id),
            func.avg(TransactionLog.fraud_probability),
            func.avg(TransactionLog.processing_time_ms),
        ).where(TransactionLog.id.in_(ids))
        totals = await db.execute(stmt)
        row = totals.one()
        cnt = float(row[0] or 0)
        avg_p = float(row[1] or 0)
        avg_ms = float(row[2] or 0)

        decisions: dict[str, int] = {}
        for d in ("APPROVED", "REVIEW", "BLOCKED"):
            q = select(func.count(TransactionLog.id)).where(
                TransactionLog.decision == d,
                TransactionLog.id.in_(ids),
            )
            decisions[d] = int((await db.execute(q)).scalar() or 0)

        return {
            "window": window,
            "count": int(cnt),
            "avg_fraud_probability": avg_p,
            "avg_processing_time_ms": avg_ms,
            "decisions": decisions,
        }

    async def get_feature_sample(
        self, db: AsyncSession, window: int = 1000
    ) -> list[list[dict]]:
        stmt = (
            select(TransactionLog.top_shap_features)
            .order_by(TransactionLog.predicted_at.desc())
            .limit(window)
        )
        res = await db.execute(stmt)
        rows = list(res.scalars().all())
        out: list[list[dict]] = []
        for raw in rows:
            if isinstance(raw, list):
                serialized: list[dict] = []
                for item in raw:
                    if isinstance(item, dict):
                        serialized.append(dict(item))
                out.append(serialized)
            else:
                out.append([])
        return out

    async def count_total(self, db: AsyncSession) -> int:
        stmt = select(func.count(TransactionLog.id))
        count = await db.execute(stmt)
        return int(count.scalar() or 0)
