"""Population Stability Index drift detection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.models.schemas import DriftReport

logger = logging.getLogger(__name__)

PSI_THRESHOLD = 0.2
PSI_WARN_THRESHOLD = 0.1
MIN_SAMPLE_SIZE = 100


class DriftDetector:
    """10-bin PSI reference vs current distributions per feature."""

    def __init__(
        self,
        reference_distributions: dict[str, dict[str, list[float]]] | None = None,
    ) -> None:
        self.reference_distributions: dict[str, dict[str, Any]] = (
            reference_distributions or {}
        )

    def compute_psi(
        self, expected_pcts: list[float], actual_pcts: list[float]
    ) -> float:
        eps = 1e-10
        psi_total = 0.0
        for ep, ap in zip(expected_pcts, actual_pcts, strict=False):
            e = ep + eps
            a = ap + eps
            psi_total += float((a - e) * np.log(a / e))
        return float(psi_total)

    def set_baseline(self, feature_data: dict[str, list[float]]) -> None:
        ref: dict[str, dict[str, Any]] = {}
        for fname, vals in feature_data.items():
            arr = np.asarray(vals, dtype=float)
            if arr.size == 0:
                continue
            lo, hi = float(arr.min()), float(arr.max())
            if lo == hi:
                hi = lo + 1e-6
            edges = np.linspace(lo, hi, 11)
            pct, _ = np.histogram(arr, bins=edges)
            pct = pct.astype(float)
            pct = pct / pct.sum() if pct.sum() else pct
            ref[fname] = {"bins": edges.tolist(), "expected_pcts": pct.tolist()}
        self.reference_distributions = ref
        logger.info("Drift baseline set for %s features.", len(ref))

    def check_drift(
        self,
        current_feature_data: dict[str, list[float]],
        window_size: int = 1000,
    ) -> DriftReport:
        now = datetime.now(timezone.utc)
        if not self.reference_distributions:
            return DriftReport(
                checked_at=now,
                window_size=window_size,
                features_with_drift=["baseline_not_set"],
                psi_scores={},
                drift_detected=False,
            )

        total_points = (
            sum(len(v) for v in current_feature_data.values())
            if current_feature_data
            else 0
        )
        if total_points < MIN_SAMPLE_SIZE:
            return DriftReport(
                checked_at=now,
                window_size=window_size,
                features_with_drift=["insufficient_sample"],
                psi_scores={},
                drift_detected=False,
            )

        psi_scores: dict[str, float] = {}
        drifting: list[str] = []

        for fname, ref in self.reference_distributions.items():
            edges = np.asarray(ref["bins"], dtype=float)
            expected = ref["expected_pcts"]
            values = np.asarray(current_feature_data.get(fname, []), dtype=float)
            if values.size < MIN_SAMPLE_SIZE:
                continue
            actual_counts, _ = np.histogram(values, bins=edges)
            actual = actual_counts.astype(float)
            actual = actual / actual.sum() if actual.sum() else actual
            exp = np.asarray(expected, dtype=float)

            psi = self.compute_psi(exp.tolist(), actual.tolist())
            psi_scores[fname] = float(psi)
            if psi > PSI_THRESHOLD:
                drifting.append(fname)

        drift_detected = bool(drifting)
        return DriftReport(
            checked_at=now,
            window_size=window_size,
            features_with_drift=drifting,
            psi_scores=psi_scores,
            drift_detected=drift_detected,
        )

    def interpret_psi(self, psi: float) -> str:
        if psi < PSI_WARN_THRESHOLD:
            return "stable"
        if psi < PSI_THRESHOLD:
            return "warning"
        return "significant_drift"
