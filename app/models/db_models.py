"""SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class TransactionLog(Base):
    """Stored prediction audit trail."""

    __tablename__ = "transaction_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transaction_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    time_offset: Mapped[float | None] = mapped_column(Float, nullable=True)
    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    model_used: Mapped[str] = mapped_column(String(30), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_cold_start: Mapped[bool] = mapped_column(Boolean, default=False)
    top_shap_features: Mapped[list] = mapped_column(JSON, default=lambda: [])
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class ModelMetadata(Base):
    """Registered trained model lineage."""

    __tablename__ = "model_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auc_roc: Mapped[float | None] = mapped_column(Float, nullable=True)
    auc_pr: Mapped[float | None] = mapped_column(Float, nullable=True)
    n_train_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fraud_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
