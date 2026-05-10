"""Curated synthetic telemetry for portfolio screenshots when the API is offline."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

# Realistic rolling-window snapshot (not claimed to be from production).
SYNTHETIC_METRICS: dict = {
    "window_size": 2000,
    "total_predictions": 2847,
    "blocked_count": 41,
    "review_count": 97,
    "approved_count": 2709,
    "fraud_rate_estimate": 0.031,
    "avg_fraud_probability": 0.082,
    "avg_processing_time_ms": 4.6,
    "model_version": "xgboost-v1-demo",
    "computed_at": datetime.now(timezone.utc).isoformat(),
}


def synthetic_transactions(n: int = 40) -> list[dict]:
    """Rows shaped like GET /api/v1/transactions for Streamlit / Plotly.

    Chronological order for time-series charts; use ``sort_for_audit_table`` for
    portfolio tables so BLOCKED/REVIEW surface at the top.
    """
    now = datetime.now(timezone.utc)
    decisions = (
        ["APPROVED"] * 22 + ["REVIEW"] * 10 + ["BLOCKED"] * 8
    )[:n]
    out: list[dict] = []
    for i in range(n):
        ts = now - timedelta(minutes=4 * (n - i))
        dec = decisions[i % len(decisions)]
        p = 0.02 + (i % 11) * 0.07
        if dec == "REVIEW":
            p = min(0.72, p + 0.35)
        if dec == "BLOCKED":
            p = min(0.96, p + 0.55)
        out.append(
            {
                "transaction_id": str(uuid.uuid4()),
                "amount": round(12.5 + (i * 37.3) % 4200, 2),
                "fraud_probability": round(p, 4),
                "decision": dec,
                "model_used": "xgboost" if i % 3 else "isolation_forest",
                "is_cold_start": i % 7 == 0,
                "explanation": "",
                "predicted_at": ts.isoformat(),
            }
        )
    return out


def sort_for_audit_table(rows: list[dict]) -> list[dict]:
    """BLOCKED / REVIEW first, then by fraud probability (portfolio readability)."""

    def key(r: dict) -> tuple[int, float, str]:
        d = str(r.get("decision", "")).upper()
        tier = 0 if d == "BLOCKED" else 1 if d == "REVIEW" else 2
        return (tier, -float(r.get("fraud_probability") or 0), str(r.get("predicted_at", "")))

    return sorted(rows, key=key)


def synthetic_health() -> dict:
    return {
        "status": "ok",
        "model_loaded": True,
        "model_version": "xgboost-v1-demo",
        "ollama_available": False,
        "db_connected": True,
        "total_predictions_served": 128_442,
        "uptime_seconds": 86_400.0,
    }
