"""Unit tests for Stripe method logic."""

import pytest

from app.stripe import parse_components
from app.openai_client import cosine_similarity


def test_parse_components_single_sentence():
    """Single sentence becomes one component."""
    assert parse_components("Hello world.") == ["Hello world."]


def test_parse_components_multiple_sentences():
    """Multiple sentences split into components."""
    text = "First sentence. Second sentence. Third sentence."
    assert parse_components(text) == ["First sentence.", "Second sentence.", "Third sentence."]


def test_parse_components_newlines():
    """Newlines split into lines, then sentences."""
    text = "Line one.\nLine two.\nLine three."
    assert parse_components(text) == ["Line one.", "Line two.", "Line three."]


def test_parse_components_empty():
    """Empty or whitespace-only returns empty list."""
    assert parse_components("") == []
    assert parse_components("   \n\n  ") == []


def test_parse_components_no_periods():
    """Prompt with no sentence-ending punctuation becomes single component."""
    text = "Just some words without periods"
    assert parse_components(text) == ["Just some words without periods"]


def test_parse_components_mixed():
    """Mixed newlines and sentences."""
    text = "Start here.\nMiddle part. More here.\nEnd."
    assert parse_components(text) == [
        "Start here.",
        "Middle part.",
        "More here.",
        "End.",
    ]


def test_cosine_similarity_identical():
    """Identical vectors return 1.0."""
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    """Orthogonal vectors return 0.0."""
    a, b = [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector():
    """Zero vector returns 0.0 (avoids division by zero)."""
    assert cosine_similarity([0.0, 0.0, 0.0], [1.0, 2.0, 3.0]) == 0.0
