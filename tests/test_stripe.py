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
    # With reverse-order sequential removal + validation:
    # Phase 1 reverse (i=2,1,0): comp 2 redundant, comps 1 & 0 essential
    # Phase 2 validation: passes → 1 of 3 redundant = 0.33
    embeddings = [
        [1.0, 0.0, 0.0],  # baseline
        [1.0, 0.0, 0.0],  # remove comp 2 → similar → redundant
        [0.0, 1.0, 0.0],  # remove comp 1 (from {0,1}) → different → essential
        [0.0, 1.0, 0.0],  # remove comp 0 (from {0,1}) → different → essential
        [1.0, 0.0, 0.0],  # validation → passes
    ]
    call_count = 0

    def mock_get_embedding(_text, **kwargs):
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

    def capture_prompt(prompt, **kwargs):
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
    # Reverse-order sequential removal + validation:
    # Phase 1: test comp 1 first (different → essential), then comp 0 (similar → redundant)
    # Phase 2: validation passes
    embeddings = [
        [1.0, 0.0, 0.0],  # baseline
        [0.0, 1.0, 0.0],  # remove comp 1 → different → essential
        [1.0, 0.0, 0.0],  # remove comp 0 → similar → redundant
        [1.0, 0.0, 0.0],  # validation → passes
    ]
    call_count = 0

    def mock_get_embedding(_text, **kwargs):
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
    # Reverse-order + validation: both comps essential at threshold 0.95
    embeddings = [
        [1.0, 0.0, 0.0],  # baseline
        [0.0, 1.0, 0.0],  # remove comp 1 → 0.0 sim → essential
        [0.93, 0.37, 0.0],  # remove comp 0 → ~0.93 sim < 0.95 → essential
        [1.0, 0.0, 0.0],  # validation → passes (both kept, same as original)
    ]
    call_count = 0

    def mock_get_embedding(_text, **kwargs):
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

    assert result["over_engineered_score"] == 0.0
    assert result["components_removed"] == []
    assert result["components_kept"] == ["A.", "B."]


def test_parse_components_list_items_kept_together():
    """List items starting with -, •, or * are kept as single components."""
    text = "Instructions:\n- Do this first. Then do that.\n- Also do this."
    assert parse_components(text) == [
        "Instructions:",
        "- Do this first. Then do that.",
        "- Also do this.",
    ]


def test_parse_components_bullet_items():
    """Bullet items with • are kept as single components."""
    text = "• POSITIVE → good things. Very favorable.\n• NEGATIVE → bad things."
    assert parse_components(text) == [
        "• POSITIVE → good things. Very favorable.",
        "• NEGATIVE → bad things.",
    ]


def test_run_stripe_analysis_recovery_adds_back_components():
    """Greedy recovery adds back essential components when validation fails."""
    # 4 components: A, B, C, D
    # Phase 1 (reverse): D, C, B each look redundant individually;
    #   A is the only one left so it's kept.
    # Phase 2: just "A" diverges from baseline → validation fails.
    # Phase 3: recovery adds back B (still fails), then C → passes.
    embeddings = [
        [1.0, 0.0, 0.0],  # baseline
        [1.0, 0.0, 0.0],  # remove D (from {A,B,C,D}) → similar → redundant
        [1.0, 0.0, 0.0],  # remove C (from {A,B,C}) → similar → redundant
        [1.0, 0.0, 0.0],  # remove B (from {A,B}) → similar → redundant
        # remove A from {A} → empty → 0.0 → A kept (no API call)
        [0.0, 1.0, 0.0],  # validation of "A" → different → fails
        [0.0, 1.0, 0.0],  # recovery: add B → "A B" → still different
        [1.0, 0.0, 0.0],  # recovery: add C → "A B C" → similar → stop
    ]
    call_count = 0

    def mock_get_embedding(_text, **kwargs):
        nonlocal call_count
        result = embeddings[call_count]
        call_count += 1
        return result

    with (
        patch("app.stripe.call_model", return_value="sample output"),
        patch("app.stripe.get_embedding", side_effect=mock_get_embedding),
    ):
        result = run_stripe_analysis("A. B. C. D.")

    assert result["over_engineered_score"] == 0.25  # 1 of 4 redundant (only D)
    assert result["components_removed"] == ["D."]
    assert result["components_kept"] == ["A.", "B.", "C."]
    assert result["total_components"] == 4


def test_run_stripe_analysis_with_api_key_passes_through():
    """run_stripe_analysis passes api_key to call_model and get_embedding."""
    with (
        patch("app.stripe.call_model", return_value="output") as mock_call,
        patch("app.stripe.get_embedding", return_value=[1.0, 0.0, 0.0]),
    ):
        run_stripe_analysis("Test.", api_key="sk-user-key")

    assert mock_call.call_count >= 1
    for call in mock_call.call_args_list:
        assert call.kwargs.get("api_key") == "sk-user-key"
