"""Unit tests for Stripe method logic."""

from unittest.mock import patch

import pytest

from app.openai_client import cosine_similarity
from app.stripe import parse_components, run_stripe_analysis


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


def test_run_stripe_analysis_empty_prompt():
    """Empty prompt returns zero score and empty component lists."""
    result = run_stripe_analysis("")
    assert result["over_engineered_score"] == 0.0
    assert result["improved_prompt"] == ""
    assert result["components_removed"] == []
    assert result["components_kept"] == []
    assert result["total_components"] == 0


def test_run_stripe_analysis_with_mocked_openai():
    """run_stripe_analysis correctly classifies redundant vs essential components."""
    # Embeddings: baseline and stripped(i=0) similar -> component 0 redundant;
    # stripped(i=1) different -> component 1 essential
    embeddings = [
        [1.0, 0.0, 0.0],  # baseline
        [1.0, 0.0, 0.0],  # stripped without component 0 (similar)
        [0.0, 1.0, 0.0],  # stripped without component 1 (different)
    ]
    call_count = 0

    def mock_get_embedding(_text):
        nonlocal call_count
        result = embeddings[call_count]
        call_count += 1
        return result

    with (
        patch("app.stripe.call_model", return_value="sample output"),
        patch("app.stripe.get_embedding", side_effect=mock_get_embedding),
    ):
        result = run_stripe_analysis("Be concise. Always use bullet points.")

    assert result["over_engineered_score"] == 0.5  # 1 of 2 redundant
    assert result["components_removed"] == ["Be concise."]
    assert result["components_kept"] == ["Always use bullet points."]
    assert result["total_components"] == 2
