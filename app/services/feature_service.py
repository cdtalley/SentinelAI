"""Feature engineering bridge for online scoring."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from app.models.schemas import TransactionInput
from ml.feature_engineering import FEATURE_COLUMNS, engineer_features

logger = logging.getLogger(__name__)


class FeatureEngineeringError(Exception):
    """Raised when engineered columns don't match training schema."""


class FeatureService:
    """Turns API payloads into model-ready matrices using the training-time scaler."""

    def __init__(self, scaler: object, feature_names: list[str]) -> None:
        self._scaler = scaler
        self._feature_names = list(feature_names)

    def build_transaction_features(self, transaction: TransactionInput) -> np.ndarray:
        row: dict[str, float] = {
            "Time": float(transaction.time),
            "Amount": float(transaction.amount),
        }
        for i in range(1, 29):
            row[f"V{i}"] = float(getattr(transaction, f"v{i}"))
        df = pd.DataFrame([row])
        feat_df, _ = engineer_features(df, scaler=self._scaler, fit_scaler=False)
        cols = list(feat_df.columns)
        if cols != self._feature_names:
            logger.error(
                "Feature mismatch. expected=%s got=%s",
                self._feature_names,
                cols,
            )
            raise FeatureEngineeringError(
                "Engineered columns do not match trained feature schema."
            )
        return feat_df.values.astype(np.float64)

    def feature_names(self) -> list[str]:
        """Ordered feature names aligned with training."""
        return list(self._feature_names)
