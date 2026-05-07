"""LLM-assisted narrative explanations with safe fallbacks."""

from __future__ import annotations

from collections import OrderedDict
from typing import Callable, TYPE_CHECKING

from app.models.schemas import PredictionResult, TransactionInput

if TYPE_CHECKING:
    from app.utils.ollama_client import OllamaClient


class ExplanationService:
    """Optional Ollama explanations with bounded in-memory LRU cache."""

    def __init__(self, ollama_client: OllamaClient, max_cache: int = 500) -> None:
        self._client = ollama_client
        self._max_cache = max_cache
        self._cache: OrderedDict[tuple[str, str], str] = OrderedDict()

    def _cache_get_set(self, key: tuple[str, str], producer: Callable[[], str]) -> str:
        if key in self._cache:
            val = self._cache.pop(key)
            self._cache[key] = val
            return val
        val = producer()
        self._cache[key] = val
        while len(self._cache) > self._max_cache:
            self._cache.popitem(last=False)
        return val

    def explain(self, result: PredictionResult, transaction: TransactionInput) -> str:
        """Return concise analyst summary; empty for approved rows."""
        if result.decision == "APPROVED":
            return ""

        def _produce() -> str:
            health = self._client.health_check()
            available = bool(health.get("available", False))

            if not available:
                return self._fallback_explanation(result)

            lines = []
            for f in result.top_shap_features:
                lines.append(
                    f"- {f.feature_name}: {f.direction} risk (impact: {abs(f.shap_value):.4f})"
                )
            shap_txt = "\n".join(lines) if lines else "- (cold start — no SHAP signals)"
            user_msg = (
                f"Transaction: ${transaction.amount:.2f} at time offset "
                f"{transaction.time:.0f}s\nDecision: {result.decision} "
                f"(probability: {result.fraud_probability:.1%})\n"
                f"Model: {result.model_used}\nTop risk signals:\n"
                f"{shap_txt}\nIs new account (cold start): {result.is_cold_start}"
            )
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a fraud analyst AI. In 2-3 concise sentences, explain "
                        "to a risk officer why this transaction was flagged. Be specific "
                        "about which signals drove the decision. Use plain English — no jargon."
                    ),
                },
                {"role": "user", "content": user_msg},
            ]
            txt = self._client.chat(messages, temperature=0.0)
            if not txt.strip():
                return self._fallback_explanation(result)
            return txt.strip()

        return self._cache_get_set(
            (result.transaction_id, result.decision),
            _produce,
        )

    def _fallback_explanation(self, result: PredictionResult) -> str:
        feats = sorted(
            result.top_shap_features,
            key=lambda x: x.abs_impact,
            reverse=True,
        )[:3]
        if not feats:
            return (
                f"This transaction was flagged ({result.decision}) with "
                f"{result.fraud_probability:.1%} fraud probability "
                "(cold-start anomaly detector — SHAP unavailable)."
            )
        parts = [f"{f.feature_name}: {f.direction}" for f in feats]
        return (
            f"This transaction was flagged ({result.decision}) with "
            f"{result.fraud_probability:.1%} fraud probability. "
            f"Key signals: {', '.join(parts)}."
        )
