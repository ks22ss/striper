"""Unit tests for Stripe method logic."""

from unittest.mock import patch

import pytest

from app.openai_client import cosine_similarity
from app.stripe import (
    _build_analysis_result,
    _build_full_prompt,
    parse_components,
    run_stripe_analysis,
)


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


def test_build_analysis_result_rounds_score():
    """_build_analysis_result rounds over_engineered_score to 2 decimals."""
    result = _build_analysis_result(0.333333, "x", [], ["x"], 1)
    assert result["over_engineered_score"] == 0.33
    assert result["improved_prompt"] == "x"
    assert result["components_removed"] == []
    assert result["components_kept"] == ["x"]
    assert result["total_components"] == 1


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


def test_build_full_prompt_without_input():
    """_build_full_prompt uses default user query when no input provided."""
    result = _build_full_prompt("Be concise.")
    assert "What can you help me with?" in result
    assert "Be concise." in result
    assert "User input:" not in result


def test_build_full_prompt_with_input():
    """_build_full_prompt includes user input when provided."""
    result = _build_full_prompt("Summarize briefly.", "This is the document to summarize.")
    assert "User input:" in result
    assert "This is the document to summarize." in result
    assert "Summarize briefly." in result
    assert "What can you help me with?" not in result


def test_run_stripe_analysis_empty_prompt():
    """Empty prompt returns zero score and empty component lists."""
    result = run_stripe_analysis("")
    assert result["over_engineered_score"] == 0.0
    assert result["improved_prompt"] == ""
    assert result["components_removed"] == []
    assert result["components_kept"] == []
    assert result["total_components"] == 0


def test_run_stripe_analysis_rounds_score():
    """Over-engineered score is rounded to 2 decimal places."""
    # 1 of 3 redundant -> 0.333... rounds to 0.33
    embeddings = [
        [1.0, 0.0, 0.0],  # baseline
        [1.0, 0.0, 0.0],  # stripped without component 0 (redundant)
        [0.0, 1.0, 0.0],  # stripped without component 1 (essential)
        [0.0, 1.0, 0.0],  # stripped without component 2 (essential)
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
        result = run_stripe_analysis("First. Second. Third.")

    assert result["over_engineered_score"] == 0.33
    assert result["total_components"] == 3


def test_run_stripe_analysis_with_input_passes_to_model():
    """run_stripe_analysis with user_input includes it in the prompt sent to the model."""
    captured_prompts = []

    def capture_prompt(prompt):
        captured_prompts.append(prompt)
        return "sample output"

    with (
        patch("app.stripe.call_model", side_effect=capture_prompt),
        patch("app.stripe.get_embedding", return_value=[1.0, 0.0, 0.0]),
    ):
        run_stripe_analysis("A.", user_input="My custom input")

    assert len(captured_prompts) >= 1
    assert "My custom input" in captured_prompts[0]
    assert "User input:" in captured_prompts[0]


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


def test_run_stripe_analysis_respects_similarity_threshold_env():
    """run_stripe_analysis uses SIMILARITY_THRESHOLD from env when set."""
    # With threshold 0.95, sim=1.0 still passes; with 0.99, sim=0.9 would fail.
    # Use embeddings where sim=0.93: with default 0.92 it's redundant, with 0.95 it's essential
    embeddings = [
        [1.0, 0.0, 0.0],  # baseline
        [0.93, 0.37, 0.0],  # stripped(i=0): cos sim ~0.93
        [0.0, 1.0, 0.0],  # stripped(i=1): different
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
        patch.dict("os.environ", {"SIMILARITY_THRESHOLD": "0.95"}),
    ):
        result = run_stripe_analysis("A. B.")

    # With threshold 0.95, 0.93 < 0.95 so component 0 is essential; component 1 also essential
    assert result["over_engineered_score"] == 0.0
    assert result["components_removed"] == []
    assert result["components_kept"] == ["A.", "B."]
