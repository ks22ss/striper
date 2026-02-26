"""Tests for FastAPI app endpoints."""

from unittest.mock import patch

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


def test_analyze_success():
    """Analyze endpoint returns result when stripe analysis succeeds."""
    mock_result = {
        "over_engineered_score": 0.25,
        "improved_prompt": "Be concise.",
        "components_removed": ["Always use bullet points."],
        "components_kept": ["Be concise."],
        "total_components": 2,
    }
    with patch("app.main.run_stripe_analysis", return_value=mock_result):
        r = client.post("/analyze", json={"prompt": "Be concise. Always use bullet points."})
    assert r.status_code == 200
    data = r.json()
    assert data["over_engineered_score"] == 0.25
    assert data["improved_prompt"] == "Be concise."
    assert "components_removed" in data
    assert "components_kept" in data


def test_analyze_with_optional_input():
    """Analyze endpoint accepts optional input and passes it to stripe analysis."""
    mock_result = {
        "over_engineered_score": 0.0,
        "improved_prompt": "Summarize briefly.",
        "components_removed": [],
        "components_kept": ["Summarize briefly."],
        "total_components": 1,
    }
    with patch("app.main.run_stripe_analysis", return_value=mock_result) as mock_run:
        r = client.post(
            "/analyze",
            json={
                "prompt": "Summarize briefly.",
                "input": "This is a long document about AI and machine learning.",
            },
        )
    assert r.status_code == 200
    mock_run.assert_called_once_with(
        "Summarize briefly.", "This is a long document about AI and machine learning."
    )
