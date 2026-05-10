"""Drift detector numerical behavior."""

from __future__ import annotations

import numpy as np

from app.monitoring.drift_detector import DriftDetector


def test_psi_identical_distributions_near_zero() -> None:
    d = DriftDetector()
    p = [0.1] * 10
    psi = d.compute_psi(p, p)
    assert abs(psi) < 1e-6


def test_psi_shifted_mass_is_positive() -> None:
    d = DriftDetector()
    expected = [0.1] * 10
    actual = [0.05, 0.05, 0.05, 0.05, 0.05, 0.15, 0.15, 0.15, 0.15, 0.15]
    psi = d.compute_psi(expected, actual)
    assert psi > 0.01


def test_no_baseline_returns_flag_not_drift() -> None:
    d = DriftDetector()
    report = d.check_drift({"f": list(np.random.randn(200))}, window_size=200)
    assert report.drift_detected is False
    assert "baseline_not_set" in report.features_with_drift
