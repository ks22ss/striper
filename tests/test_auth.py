"""Tests for auth module."""

from app.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password():
    """Password hashing produces different output each time (salt)."""
    h1 = hash_password("secret123")
    h2 = hash_password("secret123")
    assert h1 != h2
    assert len(h1) > 20


def test_verify_password():
    """Verify password matches hash."""
    h = hash_password("secret123")
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False


def test_create_and_decode_token():
    """Create token and decode returns payload."""
    token = create_access_token(data={"sub": "42"})
    assert isinstance(token, str)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert "exp" in payload


def test_decode_invalid_token():
    """Invalid token returns None."""
    assert decode_token("invalid") is None
    assert decode_token("") is None
