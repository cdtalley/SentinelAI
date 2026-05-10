"""HTTP contract tests (no external DB or model artifacts required for these)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _minimal_v() -> dict[str, float]:
    return {f"v{i}": 0.0 for i in range(1, 29)}


def test_root_returns_service_metadata(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("service") == "SentinelAI"
    assert "/docs" in data.get("docs", "")


def test_health_returns_structured_payload(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert "model_loaded" in body
    assert "db_connected" in body
    assert "ollama_available" in body
    assert "total_predictions_served" in body
    assert "uptime_seconds" in body


def test_predict_rejects_negative_amount(client: TestClient) -> None:
    payload = {"amount": -1.0, "time": 0.0, **_minimal_v()}
    r = client.post("/api/v1/predict", json=payload)
    assert r.status_code == 422
    err = r.json()
    assert "message" in err or "errors" in err


def test_predict_rejects_missing_field(client: TestClient) -> None:
    payload = {"amount": 10.0, "time": 100.0, "v1": 0.0}
    r = client.post("/api/v1/predict", json=payload)
    assert r.status_code == 422


def test_openapi_lists_core_paths(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    assert "/api/v1/health" in paths
    assert "/api/v1/health/live" in paths
    assert "/api/v1/health/ready" in paths
    assert "/api/v1/predict" in paths


def test_health_live_always_ok(client: TestClient) -> None:
    r = client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
