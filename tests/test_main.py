"""Tests for FastAPI app endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """Health endpoint returns ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root_serves_ui():
    """Root serves index.html or API message."""
    r = client.get("/")
    assert r.status_code == 200
    # Either HTML or JSON fallback
    assert "text/html" in r.headers.get("content-type", "") or "application/json" in r.headers.get(
        "content-type", ""
    )


def test_analyze_requires_prompt():
    """Analyze endpoint requires non-empty prompt."""
    r = client.post("/analyze", json={})
    assert r.status_code == 422  # Validation error
