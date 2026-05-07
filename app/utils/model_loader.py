"""Load serialized ML artifacts from disk."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import joblib

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)


class ModelNotFoundError(Exception):
    """Raised when required model artifacts are missing on disk."""


class ModelLoader:
    """Loads XGBoost, Isolation Forest, scaler, and feature name list from MODEL_DIR."""

    def __init__(self, model_dir: str, settings: Settings) -> None:
        self.model_dir = Path(model_dir)
        self._settings = settings
        self.xgboost_model: Any = None
        self.isolation_forest: Any = None
        self.scaler: Any = None
        self.feature_names: list[str] | None = None

    def load_all(self) -> dict[str, Any]:
        xgb_path = self.model_dir / self._settings.XGBOOST_MODEL_FILE
        iso_path = self.model_dir / self._settings.ISOLATION_FOREST_FILE
        scaler_path = self.model_dir / self._settings.SCALER_FILE
        feat_path = self.model_dir / self._settings.FEATURE_NAMES_FILE

        missing = [str(p) for p in (xgb_path, iso_path, scaler_path, feat_path) if not p.is_file()]
        if missing:
            raise ModelNotFoundError(
                "Model files not found. Run: python ml/train.py first."
            )

        self.xgboost_model = joblib.load(xgb_path)
        self.isolation_forest = joblib.load(iso_path)
        self.scaler = joblib.load(scaler_path)
        with open(feat_path, encoding="utf-8") as f:
            self.feature_names = json.load(f)

        return {
            "xgboost": self.xgboost_model,
            "isolation_forest": self.isolation_forest,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
        }

    def is_ready(self) -> bool:
        return (
            self.xgboost_model is not None
            and self.isolation_forest is not None
            and self.scaler is not None
            and self.feature_names is not None
        )
