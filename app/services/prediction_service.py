"""Batch and single-record fraud scoring orchestration."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import numpy as np
import shap

from app.models.schemas import PredictionResult, SHAPFeature, TransactionInput

if TYPE_CHECKING:
    from app.config import Settings
    from app.services.feature_service import FeatureService


class PredictionService:
    """Core inference engine: XGBoost for warm path, Isolation Forest cold-start."""

    def __init__(
        self,
        xgb_model: Any,
        iso_forest: Any,
        feature_service: FeatureService,
        settings: Settings,
    ) -> None:
        self._xgb_model = xgb_model
        self._iso_forest = iso_forest
        self._feature_service = feature_service
        self._settings = settings
        self._shap_explainer: Any = None

    def _explain_xgb_row(self, features: np.ndarray) -> np.ndarray:
        if self._shap_explainer is None:
            self._shap_explainer = shap.TreeExplainer(self._xgb_model)
        vals = self._shap_explainer.shap_values(features)
        # Binary classifier: TreeExplainer may return list[class] or ndarray
        if isinstance(vals, list):
            vals = vals[1]
        row = vals[0] if vals.ndim > 1 else vals
        return np.asarray(row, dtype=float)

    def predict(
        self,
        transaction: TransactionInput,
        is_cold_start: bool,
    ) -> PredictionResult:
        t0 = time.perf_counter()
        features = self._feature_service.build_transaction_features(transaction)
        names = self._feature_service.feature_names()

        if is_cold_start:
            iso_score = float(self._iso_forest.score_samples(features)[0])
            lo = self._settings.ISO_SCORE_MIN
            hi = self._settings.ISO_SCORE_MAX
            span = hi - lo
            normalized = (
                (iso_score - lo) / span
                if span != 0
                else 0.5
            )
            fraud_probability = float(1.0 - normalized)
            fraud_probability = max(0.0, min(1.0, fraud_probability))
            model_used = "isolation_forest"
            top_shap: list[SHAPFeature] = []
        else:
            probs = self._xgb_model.predict_proba(features)[0]
            fraud_probability = float(probs[1])
            model_used = "xgboost"
            shap_row = self._explain_xgb_row(features)
            pairs = list(zip(names, shap_row, strict=False))
            pairs_sorted = sorted(pairs, key=lambda x: abs(x[1]), reverse=True)[
                : self._settings.TOP_K_SHAP_FEATURES
            ]
            top_shap = []
            for name, sv in pairs_sorted:
                direction: str = (
                    "increases_risk" if sv > 0 else "decreases_risk"
                )
                top_shap.append(
                    SHAPFeature(
                        feature_name=name,
                        shap_value=float(sv),
                        direction=direction,  # type: ignore[arg-type]
                        abs_impact=float(abs(sv)),
                    )
                )

        if fraud_probability >= self._settings.FRAUD_THRESHOLD_BLOCK:
            decision = "BLOCKED"
        elif fraud_probability >= self._settings.FRAUD_THRESHOLD_REVIEW:
            decision = "REVIEW"
        else:
            decision = "APPROVED"

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return PredictionResult(
            transaction_id=transaction.transaction_id,
            amount=float(transaction.amount),
            fraud_probability=fraud_probability,
            decision=decision,  # type: ignore[arg-type]
            model_used=model_used,  # type: ignore[arg-type]
            model_version=self._settings.MODEL_VERSION,
            top_shap_features=top_shap,
            is_cold_start=is_cold_start,
            processing_time_ms=float(elapsed_ms),
        )

    def batch_predict(
        self,
        transactions: list[TransactionInput],
    ) -> list[PredictionResult]:
        """Score each payload independently."""
        from app.utils.cold_start import is_demo_cold_start

        return [self.predict(tx, is_demo_cold_start(tx)) for tx in transactions]
