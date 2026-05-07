"""Pydantic request/response models."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class TransactionInput(BaseModel):
    """Single transaction scoring payload."""

    transaction_id: str = Field(default_factory=lambda: str(uuid4()))
    time: float = Field(description="Seconds elapsed since first transaction in dataset")
    amount: float = Field(gt=0, description="Transaction amount in USD")
    v1: float
    v2: float
    v3: float
    v4: float
    v5: float
    v6: float
    v7: float
    v8: float
    v9: float
    v10: float
    v11: float
    v12: float
    v13: float
    v14: float
    v15: float
    v16: float
    v17: float
    v18: float
    v19: float
    v20: float
    v21: float
    v22: float
    v23: float
    v24: float
    v25: float
    v26: float
    v27: float
    v28: float

    @model_validator(mode="after")
    def validate_amount_range(self) -> TransactionInput:
        if self.amount > 25000:
            logger.warning(
                "Unusually large amount for transaction_id=%s: %s",
                self.transaction_id,
                self.amount,
            )
        return self


class SHAPFeature(BaseModel):
    """One SHAP contribution for explanation."""

    feature_name: str
    shap_value: float
    direction: Literal["increases_risk", "decreases_risk"]
    abs_impact: float


class PredictionResult(BaseModel):
    """Model output plus metadata."""

    transaction_id: str
    amount: float
    fraud_probability: float
    decision: Literal["APPROVED", "REVIEW", "BLOCKED"]
    model_used: Literal["xgboost", "isolation_forest"]
    model_version: str
    top_shap_features: list[SHAPFeature]
    is_cold_start: bool
    processing_time_ms: float
    predicted_at: datetime = Field(default_factory=datetime.utcnow)


class PredictionWithExplanation(PredictionResult):
    """Prediction plus optional narrative explanation."""

    explanation: str = ""


class BatchPredictionRequest(BaseModel):
    """Batch scoring (max 100 rows)."""

    transactions: list[TransactionInput] = Field(max_length=100)


class BatchPredictionResponse(BaseModel):
    """Batch scoring response."""

    results: list[PredictionWithExplanation]
    total: int
    blocked_count: int
    review_count: int
    approved_count: int
    processing_time_ms: float


class TransactionRecord(BaseModel):
    """Slim record for dashboards and listings."""

    transaction_id: str
    amount: float
    fraud_probability: float
    decision: str
    model_used: str
    is_cold_start: bool
    explanation: str
    predicted_at: datetime


class DriftReport(BaseModel):
    """PSI-based drift diagnostics."""

    checked_at: datetime
    window_size: int
    features_with_drift: list[str]
    psi_scores: dict[str, float]
    drift_detected: bool


class PerformanceMetrics(BaseModel):
    """Rolling performance snapshot."""

    window_size: int
    total_predictions: int
    blocked_count: int
    review_count: int
    approved_count: int
    fraud_rate_estimate: float
    avg_fraud_probability: float
    avg_processing_time_ms: float
    model_version: str
    computed_at: datetime


class HealthResponse(BaseModel):
    """Liveness/readiness envelope."""

    status: str
    model_loaded: bool
    model_version: str
    ollama_available: bool
    db_connected: bool
    total_predictions_served: int
    uptime_seconds: float
