"""Application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. All thresholds and tunables live here — no magic numbers in routes."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3"
    OLLAMA_ENABLED: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinelai"
    SYNC_DATABASE_URL: str = "postgresql://sentinel:sentinel@localhost:5432/sentinelai"

    MODEL_DIR: str = "./app/models/ml"
    XGBOOST_MODEL_FILE: str = "xgboost_fraud.pkl"
    ISOLATION_FOREST_FILE: str = "isolation_forest.pkl"
    SCALER_FILE: str = "scaler.pkl"
    FEATURE_NAMES_FILE: str = "feature_names.json"
    MODEL_VERSION: str = "v1.0"

    FRAUD_THRESHOLD_BLOCK: float = 0.75
    FRAUD_THRESHOLD_REVIEW: float = 0.35
    COLD_START_MIN_TRANSACTIONS: int = 5
    TOP_K_SHAP_FEATURES: int = 5

    DRIFT_PSI_THRESHOLD: float = 0.2
    DRIFT_CHECK_WINDOW: int = 1000

    MAX_EXPLANATION_CACHE: int = 500
    WEBSOCKET_HEARTBEAT_SECONDS: int = 25
    API_RATE_LIMIT_PER_MINUTE: int = 1000

    # Isolation Forest score normalization (serving cold-start path)
    ISO_SCORE_MIN: float = -0.5
    ISO_SCORE_MAX: float = 0.1


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton for dependency injection."""
    return Settings()
