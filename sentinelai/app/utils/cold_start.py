"""Heuristic demo cold-start detector (no account IDs in the public API payload)."""

from __future__ import annotations

from app.models.schemas import TransactionInput


def is_demo_cold_start(transaction: TransactionInput) -> bool:
    """Return True when the demo treats the transaction as a cold-start anomaly path."""
    return transaction.time < 3600 and transaction.amount < 10.0
