"""SentinelAI ASGI entrypoint — fraud detection API + WebSocket alerts."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import Settings, get_settings as load_settings
from app.db.database import init_db
from app.dependencies import wire_application
from app.limiter import limiter
from app.modules.logging_config import configure_logging
from app.monitoring.drift_detector import DriftDetector
from app.monitoring.performance_tracker import PerformanceTracker
from app.routers import health, predict, transactions, websocket
from app.services.alert_service import AlertService
from app.services.explanation_service import ExplanationService
from app.services.feature_service import FeatureService
from app.services.prediction_service import PredictionService
from app.db.transaction_repo import TransactionRepository
from app.utils.model_loader import ModelLoader, ModelNotFoundError
from app.utils.ollama_client import OllamaClient

logger = logging.getLogger(__name__)
API_PREFIX = "/api/v1"


def _cors_allow_origins(settings: Settings) -> list[str]:
    raw = settings.CORS_ORIGINS.strip()
    if raw == "*":
        return ["*"]
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins if origins else ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_settings()
    configure_logging(cfg)
    ollama = OllamaClient(cfg.OLLAMA_BASE_URL, cfg.LLM_MODEL, cfg.OLLAMA_ENABLED)
    loader = ModelLoader(cfg.MODEL_DIR, cfg)
    models_ok = False
    feature_svc: FeatureService | None = None
    pred_svc: PredictionService | None = None
    try:
        loader.load_all()
        models_ok = True
        feature_svc = FeatureService(loader.scaler, list(loader.feature_names or []))
        pred_svc = PredictionService(
            loader.xgboost_model,
            loader.isolation_forest,
            feature_svc,
            cfg,
        )
        logger.info("ML artifacts loaded from %s", cfg.MODEL_DIR)
    except ModelNotFoundError as exc:
        logger.critical("%s", exc)

    explanation = ExplanationService(ollama, cfg.MAX_EXPLANATION_CACHE)
    tracker = PerformanceTracker(window_size=max(cfg.DRIFT_CHECK_WINDOW, 1000))
    tracker.set_model_version(cfg.MODEL_VERSION)
    drift = DriftDetector()
    repo = TransactionRepository()
    alerts = AlertService()

    try:
        await init_db()
        logger.info("Database schema ensured.")
    except Exception as exc:
        logger.critical(
            "PostgreSQL connection failed (%s). API will degrade until DB is up.",
            type(exc).__name__,
        )

    wire_application(
        settings=cfg,
        ollama=ollama,
        model_loader=loader,
        feature_svc=feature_svc,
        prediction_svc=pred_svc,
        explanation_svc=explanation,
        alert_svc=alerts,
        performance=tracker,
        drift=drift,
        txn_repo=repo,
        model_ready=models_ok,
    )
    logger.info(
        "SentinelAI online | models=%s | model_version=%s",
        models_ok,
        cfg.MODEL_VERSION,
    )
    yield
    logger.info("SentinelAI shutting down")


app = FastAPI(
    title="SentinelAI",
    description="Real-Time Fraud Detection — local ML, zero paid API keys",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "%s %s failed after %.2fms id=%s",
            request.method,
            request.url.path,
            duration_ms,
            correlation_id,
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = correlation_id
    logger.info(
        "%s %s -> %s in %.2fms id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        correlation_id,
    )
    return response


_startup_settings = load_settings()
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(_startup_settings),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _http_detail_payload(detail: object) -> dict:
    if isinstance(detail, dict):
        return dict(detail)
    if isinstance(detail, str):
        return {"message": detail}
    return {"message": str(detail)}


def _correlation_id(request: Request) -> str:
    return request.headers.get("X-Request-ID") or str(uuid.uuid4())


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    rid = _correlation_id(request)
    return JSONResponse(
        status_code=422,
        headers={"X-Request-ID": rid},
        content={
            "message": "Request validation failed",
            "errors": exc.errors(),
            "request_id": rid,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    rid = _correlation_id(request)
    payload = dict(_http_detail_payload(exc.detail))
    payload.setdefault("request_id", rid)
    return JSONResponse(
        status_code=exc.status_code,
        headers={"X-Request-ID": rid},
        content=payload,
    )


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    """Last-resort handler: never leak stack traces unless explicitly allowed."""
    logger.exception("Unhandled application error")
    rid = _correlation_id(request)
    settings = load_settings()
    expose = settings.EXPOSE_ERROR_DETAILS or settings.APP_ENV == "development"
    body: dict = {
        "message": "Internal server error.",
        "error": type(exc).__name__,
        "request_id": rid,
    }
    if expose:
        body["technical"] = str(exc)
    return JSONResponse(status_code=500, content=body, headers={"X-Request-ID": rid})


app.include_router(health.router, prefix=API_PREFIX)
app.include_router(predict.router, prefix=f"{API_PREFIX}/predict")
app.include_router(transactions.router, prefix=f"{API_PREFIX}/transactions")
app.include_router(websocket.router, prefix=f"{API_PREFIX}/ws")


@app.get("/")
@limiter.exempt
async def root():
    return {
        "service": "SentinelAI",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": f"{API_PREFIX}/health",
        "health_live": f"{API_PREFIX}/health/live",
        "health_ready": f"{API_PREFIX}/health/ready",
    }
