"""Tests for FastAPI app endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.auth import get_current_user
from app.main import app

client = TestClient(app)


def test_app_imports_with_auth_dependencies():
    """Regression: app imports require bcrypt, python-jose, email-validator in requirements.txt."""
    from app.auth import hash_password

    assert callable(hash_password)


# Fake user for protected route tests (avoids DB setup)
FAKE_USER = {"id": 1, "username": "testuser", "email": "test@example.com"}


async def _fake_get_current_user():
    return FAKE_USER


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


def test_root_ui_includes_reanalyze_from_history():
    """Root UI includes re-analyze-from-history feature when serving HTML."""
    r = client.get("/")
    assert r.status_code == 200
    if "text/html" in r.headers.get("content-type", ""):
        assert "Click to re-analyze" in r.text
        assert "history-item" in r.text


def test_root_html_includes_analysis_duration_display():
    """UI includes analysis duration display logic (Analyzed in X.Xs)."""
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "Analyzed in" in html
    assert "durationSec" in html or "startTime" in html


def test_ui_includes_copy_and_history_reload():
    """Served UI includes Copy button and history click-to-reload elements."""
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "Copy" in html
    assert "copy-improved-btn" in html
    assert "history-item" in html or "Click to re-analyze" in html


def test_analyze_unauthorized():
    """Analyze endpoint requires authentication."""
    r = client.post("/analyze", json={"prompt": "Hello world."})
    assert r.status_code == 401


def test_analyze_requires_prompt():
    """Analyze endpoint requires non-empty prompt."""
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        r = client.post("/analyze", json={})
        assert r.status_code == 422  # Validation error
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_analyze_success():
    """Analyze endpoint returns result when stripe analysis succeeds."""
    mock_result = {
        "over_engineered_score": 0.25,
        "improved_prompt": "Be concise.",
        "components_removed": ["Always use bullet points."],
        "components_kept": ["Be concise."],
        "total_components": 2,
    }
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        with (
            patch("app.main.run_stripe_analysis", return_value=mock_result),
            patch("app.main.add_prompt_history"),
        ):
            r = client.post("/analyze", json={"prompt": "Be concise. Always use bullet points."})
        assert r.status_code == 200
        data = r.json()
        assert data["over_engineered_score"] == 0.25
        assert data["improved_prompt"] == "Be concise."
        assert "components_removed" in data
        assert "components_kept" in data
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_register_success():
    """Register creates user and returns token."""
    with (
        patch("app.main.get_user_by_username", return_value=None),
        patch("app.main.get_user_by_email", return_value=None),
        patch("app.main.create_user", return_value=42),
        patch("app.main.hash_password", return_value="hashed"),
        patch("app.main.create_access_token", return_value="jwt-token-123"),
    ):
        r = client.post(
            "/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["access_token"] == "jwt-token-123"
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "newuser"
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["id"] == 42


def test_register_username_taken():
    """Register fails when username already exists."""
    with patch("app.main.get_user_by_username", return_value={"id": 1}):
        r = client.post(
            "/register",
            json={
                "username": "taken",
                "email": "new@example.com",
                "password": "password123",
            },
        )
    assert r.status_code == 400
    assert "Username already registered" in r.json()["detail"]


def test_login_success():
    """Login returns token for valid credentials."""
    with (
        patch(
            "app.main.authenticate_user",
            return_value={"id": 1, "username": "user", "email": "user@example.com"},
        ),
        patch("app.main.create_access_token", return_value="jwt-token"),
    ):
        r = client.post("/login", json={"username": "user", "password": "secret"})
    assert r.status_code == 200
    assert r.json()["access_token"] == "jwt-token"


def test_login_invalid():
    """Login fails for invalid credentials."""
    with patch("app.main.authenticate_user", return_value=None):
        r = client.post("/login", json={"username": "user", "password": "wrong"})
    assert r.status_code == 401
    assert "Incorrect" in r.json()["detail"]


def test_history_requires_auth():
    """History endpoint requires authentication."""
    r = client.get("/history")
    assert r.status_code == 401


def test_history_success():
    """History returns user's prompt records."""
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        with patch(
            "app.main.get_prompt_history",
            return_value=[
                {
                    "id": 1,
                    "prompt": "Be nice.",
                    "over_engineered_score": 0.0,
                    "improved_prompt": "Be nice.",
                    "created_at": "2026-02-26 10:00:00",
                },
            ],
        ):
            r = client.get("/history")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["prompt"] == "Be nice."
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_history_rejects_limit_zero():
    """History rejects limit=0 (SQLite LIMIT 0 is pointless; validate ge=1)."""
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        r = client.get("/history?limit=0")
        assert r.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_history_rejects_negative_limit():
    """History rejects negative limit (SQLite LIMIT -1 returns all rows = DoS)."""
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        r = client.get("/history?limit=-1")
        assert r.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_history_rejects_limit_over_max():
    """History rejects limit > 100 to cap response size."""
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        r = client.get("/history?limit=500")
        assert r.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_history_accepts_valid_limit():
    """History accepts limit within 1..100 and passes to get_prompt_history."""
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        with patch("app.main.get_prompt_history", return_value=[]) as mock_get:
            r = client.get("/history?limit=10")
        assert r.status_code == 200
        mock_get.assert_called_once_with(1, limit=10)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_analyze_with_optional_input():
    """Analyze endpoint accepts optional input and passes it to stripe analysis."""
    mock_result = {
        "over_engineered_score": 0.0,
        "improved_prompt": "Summarize briefly.",
        "components_removed": [],
        "components_kept": ["Summarize briefly."],
        "total_components": 1,
    }
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        with (
            patch("app.main.run_stripe_analysis", return_value=mock_result) as mock_run,
            patch("app.main.add_prompt_history"),
        ):
            r = client.post(
                "/analyze",
                json={
                    "prompt": "Summarize briefly.",
                    "input": "This is a long document about AI and machine learning.",
                },
            )
        assert r.status_code == 200
        mock_run.assert_called_once_with(
            "Summarize briefly.",
            user_input="This is a long document about AI and machine learning.",
            api_key=None,
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_analyze_with_api_key_in_request():
    """Analyze passes api_key from request to stripe analysis."""
    mock_result = {
        "over_engineered_score": 0.0,
        "improved_prompt": "Test.",
        "components_removed": [],
        "components_kept": ["Test."],
        "total_components": 1,
    }
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        with (
            patch("app.main.run_stripe_analysis", return_value=mock_result) as mock_run,
            patch("app.main.add_prompt_history"),
        ):
            r = client.post(
                "/analyze",
                json={"prompt": "Test.", "api_key": "sk-user-provided-key"},
            )
        assert r.status_code == 200
        mock_run.assert_called_once_with("Test.", user_input=None, api_key="sk-user-provided-key")
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_analyze_empty_api_key_treated_as_none():
    """Empty or whitespace api_key is treated as None (uses env fallback)."""
    mock_result = {
        "over_engineered_score": 0.0,
        "improved_prompt": "Test.",
        "components_removed": [],
        "components_kept": ["Test."],
        "total_components": 1,
    }
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    try:
        with (
            patch("app.main.run_stripe_analysis", return_value=mock_result) as mock_run,
            patch("app.main.add_prompt_history"),
        ):
            r = client.post("/analyze", json={"prompt": "Test.", "api_key": "   "})
        assert r.status_code == 200
        mock_run.assert_called_once_with("Test.", user_input=None, api_key=None)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
