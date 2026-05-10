"""Pytest fixtures."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.dependencies import require_prediction_service
from app.main import app


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deterministic, non-flaky defaults for CI."""
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("AUTH_MODE", "none")
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """Context manager ensures ASGI lifespan (model wiring, DB init hooks) runs."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def client_with_predict_stub(client: TestClient) -> TestClient:
    """Stub scoring dependency so request-body validation (422) can run without artifacts."""
    app.dependency_overrides[require_prediction_service] = lambda: MagicMock()
    yield client
    app.dependency_overrides.pop(require_prediction_service, None)
