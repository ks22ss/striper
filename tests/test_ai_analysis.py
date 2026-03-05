"""Tests for AI-based prompt analysis."""

from unittest.mock import patch

from app.ai_analysis import run_ai_analysis


def test_run_ai_analysis_empty_prompt():
    """Empty prompt returns zero score and empty fields."""
    result = run_ai_analysis("")
    assert result["over_engineered_score"] == 0.0
    assert result["improved_prompt"] == ""
    assert result["over_engineered_explanation"] == ""
    assert result["components_removed"] == []
    assert result["components_kept"] == []
    assert result["total_components"] == 0


def test_run_ai_analysis_whitespace_prompt():
    """Whitespace-only prompt returns zero score."""
    result = run_ai_analysis("   \n  ")
    assert result["over_engineered_score"] == 0.0
    assert result["improved_prompt"] == ""


def test_run_ai_analysis_returns_simplified_and_explanation():
    """run_ai_analysis returns simplified prompt and explanation from AI."""
    mock_response = {
        "simplified_prompt": "Be concise.",
        "over_engineered_explanation": "The 'Always use bullet points' instruction is redundant.",
        "over_engineered_score": 0.5,
    }
    with patch("app.ai_analysis.call_model_json", return_value=mock_response):
        result = run_ai_analysis("Be concise. Always use bullet points.")

    assert result["improved_prompt"] == "Be concise."
    assert result["over_engineered_explanation"] == (
        "The 'Always use bullet points' instruction is redundant."
    )
    assert result["over_engineered_score"] == 0.5
    assert result["components_removed"] == []
    assert result["components_kept"] == []
    assert result["total_components"] == 0


def test_run_ai_analysis_passes_user_input():
    """run_ai_analysis passes user_input to the model."""
    mock_response = {
        "simplified_prompt": "Summarize.",
        "over_engineered_explanation": "OK",
        "over_engineered_score": 0.0,
    }
    with patch("app.ai_analysis.call_model_json", return_value=mock_response) as mock_call:
        run_ai_analysis("Summarize briefly.", user_input="Long document...")

    call_args = mock_call.call_args
    assert "Long document" in call_args[0][0]


def test_run_ai_analysis_passes_api_key():
    """run_ai_analysis passes api_key to call_model_json."""
    mock_response = {
        "simplified_prompt": "Test",
        "over_engineered_explanation": "",
        "over_engineered_score": 0.0,
    }
    with patch("app.ai_analysis.call_model_json", return_value=mock_response) as mock_call:
        run_ai_analysis("Test.", api_key="sk-user-key")

    mock_call.assert_called_once()
    assert mock_call.call_args[1]["api_key"] == "sk-user-key"


def test_run_ai_analysis_fallback_when_json_fails():
    """When call_model_json fails, fallback to call_model and parse JSON from text."""
    raw_json = (
        '{"simplified_prompt": "Minimal.", "over_engineered_explanation": '
        '"Some redundancy.", "over_engineered_score": 0.3}'
    )
    with (
        patch("app.ai_analysis.call_model_json", side_effect=ValueError("JSON not supported")),
        patch("app.ai_analysis.call_model", return_value=raw_json),
    ):
        result = run_ai_analysis("Verbose prompt here.")

    assert result["improved_prompt"] == "Minimal."
    assert result["over_engineered_explanation"] == "Some redundancy."
    assert result["over_engineered_score"] == 0.3


def test_run_ai_analysis_invalid_score_derives_from_length():
    """When AI returns invalid score, derive from length reduction."""
    mock_response = {
        "simplified_prompt": "Hi",
        "over_engineered_explanation": "Very verbose.",
        "over_engineered_score": "invalid",
    }
    with patch("app.ai_analysis.call_model_json", return_value=mock_response):
        result = run_ai_analysis("Hello world this is a very long prompt with many words.")

    # orig_len >> new_len => high score
    assert 0 <= result["over_engineered_score"] <= 1
    assert result["improved_prompt"] == "Hi"


def test_run_ai_analysis_rounds_score():
    """Over-engineered score is rounded to 2 decimal places."""
    mock_response = {
        "simplified_prompt": "X",
        "over_engineered_explanation": "",
        "over_engineered_score": 0.33333,
    }
    with patch("app.ai_analysis.call_model_json", return_value=mock_response):
        result = run_ai_analysis("X")
    assert result["over_engineered_score"] == 0.33
