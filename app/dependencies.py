"""Dependency injection surface for FastAPI routes."""

from __future__ import annotations

from fastapi import HTTPException

from app.config import Settings
from app.config import get_settings as load_settings
from app.db.database import get_db as _database_get_db
from app.db.transaction_repo import TransactionRepository
from app.monitoring.drift_detector import DriftDetector
from app.monitoring.performance_tracker import PerformanceTracker
from app.services.alert_service import AlertService
from app.services.explanation_service import ExplanationService
from app.services.feature_service import FeatureService
from app.services.prediction_service import PredictionService
from app.utils.model_loader import ModelLoader
from app.utils.ollama_client import OllamaClient

IS_MODEL_READY: bool = False

_settings_instance: Settings | None = None
_ollama_client: OllamaClient | None = None
_model_loader: ModelLoader | None = None
_feature_service: FeatureService | None = None
_prediction_service: PredictionService | None = None
_explanation_service: ExplanationService | None = None
_alert_service: AlertService | None = None
_performance_tracker: PerformanceTracker | None = None
_drift_detector: DriftDetector | None = None
_transaction_repo: TransactionRepository | None = None


def wire_application(
    *,
    settings: Settings | None = None,
    ollama: OllamaClient | None = None,
    model_loader: ModelLoader | None = None,
    feature_svc: FeatureService | None = None,
    prediction_svc: PredictionService | None = None,
    explanation_svc: ExplanationService | None = None,
    alert_svc: AlertService | None = None,
    performance: PerformanceTracker | None = None,
    drift: DriftDetector | None = None,
    txn_repo: TransactionRepository | None = None,
    model_ready: bool = False,
) -> None:
    """Wire singletons from the ASGI lifespan hook."""
    global IS_MODEL_READY, _settings_instance, _ollama_client, _model_loader
    global _feature_service, _prediction_service, _explanation_service
    global _alert_service, _performance_tracker, _drift_detector, _transaction_repo

    IS_MODEL_READY = model_ready
    if settings is not None:
        _settings_instance = settings
    if ollama is not None:
        _ollama_client = ollama
    if model_loader is not None:
        _model_loader = model_loader
    if feature_svc is not None:
        _feature_service = feature_svc
    if prediction_svc is not None:
        _prediction_service = prediction_svc
    if explanation_svc is not None:
        _explanation_service = explanation_svc
    if alert_svc is not None:
        _alert_service = alert_svc
    if performance is not None:
        _performance_tracker = performance
    if drift is not None:
        _drift_detector = drift
    if txn_repo is not None:
        _transaction_repo = txn_repo


def clear_application_wiring() -> None:
    """Reset singleton pointers (mostly for tests)."""
    global IS_MODEL_READY, _settings_instance, _ollama_client, _model_loader
    global _feature_service, _prediction_service, _explanation_service
    global _alert_service, _performance_tracker, _drift_detector, _transaction_repo

    IS_MODEL_READY = False
    _settings_instance = None
    _ollama_client = None
    _model_loader = None
    _feature_service = None
    _prediction_service = None
    _explanation_service = None
    _alert_service = None
    _performance_tracker = None
    _drift_detector = None
    _transaction_repo = None


def get_settings_sync() -> Settings:
    """Depends() provider for pydantic-settings."""
    if _settings_instance is not None:
        return _settings_instance
    return load_settings()


def get_ollama_client() -> OllamaClient:
    if _ollama_client is None:
        raise HTTPException(status_code=503, detail={"message": "Ollama client not wired."})
    return _ollama_client


def get_model_loader_dep() -> ModelLoader:
    if _model_loader is None:
        raise HTTPException(status_code=503, detail={"message": "Model loader missing."})
    return _model_loader


def require_prediction_service() -> PredictionService:
    if _prediction_service is None or not IS_MODEL_READY:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Models are not trained or failed to load on disk.",
                "action": "Run: python ml/train.py (see README)",
                "docs_url": "/docs",
            },
        )
    return _prediction_service


def get_explanation_service() -> ExplanationService:
    if _explanation_service is None:
        raise HTTPException(
            status_code=503,
            detail={"message": "Explanation pipeline not initialized."},
        )
    return _explanation_service


def get_alert_service() -> AlertService:
    if _alert_service is None:
        raise HTTPException(
            status_code=503,
            detail={"message": "Alert broadcaster not initialized."},
        )
    return _alert_service


def get_performance_tracker() -> PerformanceTracker:
    if _performance_tracker is None:
        raise HTTPException(
            status_code=503,
            detail={"message": "Performance tracker not initialized."},
        )
    return _performance_tracker


def get_drift_detector() -> DriftDetector:
    if _drift_detector is None:
        raise HTTPException(
            status_code=503,
            detail={"message": "Drift detector missing."},
        )
    return _drift_detector


def get_transaction_repo() -> TransactionRepository:
    if _transaction_repo is None:
        raise HTTPException(
            status_code=503,
            detail={"message": "Persistence layer missing."},
        )
    return _transaction_repo


get_db = _database_get_db


def peek_ollama_client() -> OllamaClient | None:
    """Synchronous accessor for websocket / telemetry without HTTP semantics."""
    return _ollama_client


def peek_model_loader() -> ModelLoader | None:
    """Non-raising model loader accessor for readiness checks."""
    return _model_loader


def peek_is_model_ready() -> bool:
    return IS_MODEL_READY


def require_alert_service_sync() -> AlertService:
    if _alert_service is None:
        raise RuntimeError("AlertService wired after startup")
    return _alert_service
