"""Synchronous Ollama client using requests — optional explanations, never fails the API."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class OllamaUnavailableError(Exception):
    """Raised internally for logging only; never propagated to HTTP routes."""


class OllamaClient:
    """Minimal chat + health client for local Ollama at OLLAMA_BASE_URL."""

    def __init__(self, base_url: str, model: str, enabled: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.enabled = enabled

    def chat(self, messages: list[dict[str, Any]], temperature: float = 0.1) -> str:
        if not self.enabled:
            return ""
        url = f"{self.base_url}/api/chat"
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                resp = requests.post(url, json=body, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                return str(data.get("message", {}).get("content", ""))
            except Exception as e:
                last_err = e
                logger.warning(
                    "Ollama chat failed (attempt %s/3): %s",
                    attempt + 1,
                    e,
                    exc_info=False,
                )
                if attempt < 2:
                    time.sleep(1)
        try:
            raise OllamaUnavailableError(str(last_err)) from last_err
        except OllamaUnavailableError:
            logger.warning("Ollama unavailable after retries; returning empty explanation.")
        return ""

    def health_check(self) -> dict[str, Any]:
        if not self.enabled:
            return {"available": False, "reason": "disabled"}
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return {"available": True, "models": models}
        except Exception as e:
            logger.debug("Ollama health check failed: %s", e)
            return {"available": False, "reason": str(e)}
