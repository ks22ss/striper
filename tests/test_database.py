"""Tests for database module."""

import tempfile
from pathlib import Path

import pytest

from app.auth import hash_password
from app.database import (
    add_prompt_history,
    create_user,
    get_prompt_history,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    init_db,
)


@pytest.fixture
def temp_db(monkeypatch):
    """Use a temporary database file for tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    try:
        monkeypatch.setattr("app.database.DB_PATH", path)
        init_db()
        yield path
    finally:
        path.unlink(missing_ok=True)


def test_init_db_creates_tables(temp_db):
    """init_db creates users and prompt_history tables."""
    # Tables exist if we can insert
    user_id = create_user("u1", "u1@x.com", hash_password("p"))
    assert user_id > 0


def test_create_user_and_fetch(temp_db):
    """Create user and fetch by username and id."""
    pw_hash = hash_password("secret")
    user_id = create_user("alice", "alice@example.com", pw_hash)
    assert user_id > 0

    user = get_user_by_username("alice")
    assert user is not None
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
    assert user["id"] == user_id

    user2 = get_user_by_id(user_id)
    assert user2 is not None
    assert user2["username"] == "alice"

    assert get_user_by_email("alice@example.com") is not None
    assert get_user_by_username("bob") is None


def test_add_and_get_prompt_history(temp_db):
    """Add prompt history and retrieve it."""
    pw_hash = hash_password("p")
    user_id = create_user("u", "u@x.com", pw_hash)

    add_prompt_history(user_id, "Be nice.", 0.25, "Be nice.")
    add_prompt_history(user_id, "Be concise.", 0.5, "Be concise.")

    rows = get_prompt_history(user_id, limit=10)
    assert len(rows) == 2
    prompts = [r["prompt"] for r in rows]
    assert "Be nice." in prompts
    assert "Be concise." in prompts
