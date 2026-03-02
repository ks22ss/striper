"""AI-based prompt analysis: simplify prompt and explain over-engineered areas.

Replaces the Stripe method with a single AI call that outputs:
- simplified_prompt: a cleaner, minimal version of the prompt
- over_engineered_explanation: what parts are over-engineered and why
- over_engineered_score: 0-1 estimate of how over-engineered the prompt is
"""

import json
import re

from app.openai_client import call_model, call_model_json

AI_ANALYSIS_SYSTEM = """You are an expert at analyzing AI prompts for over-engineering.
Over-engineering means: unnecessary instructions, redundant constraints, excessive formatting rules,
or instructions that add little value compared to their verbosity.

Analyze the user's prompt and respond with valid JSON only, no other text.
Use this exact structure:
{
  "simplified_prompt": "A concise, minimal version of the prompt that keeps the core intent.",
  "over_engineered_explanation": "What is over-engineered and why (redundant/excessive parts).",
  "over_engineered_score": 0.5
}

over_engineered_score: float 0-1 where 0 = optimal/minimal, 1 = heavily over-engineered.
Be concise in simplified_prompt and specific in over_engineered_explanation."""


def _parse_json_fallback(text: str) -> dict:
    """Extract JSON from text if response_format failed (e.g. model doesn't support it)."""
    text = text.strip()
    # Try to find JSON block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def run_ai_analysis(
    prompt: str,
    user_input: str | None = None,
    api_key: str | None = None,
) -> dict:
    """
    Run AI-based analysis: ask the model to simplify the prompt and explain over-engineered areas.

    Returns dict with:
      over_engineered_score, improved_prompt, over_engineered_explanation,
      components_removed, components_kept, total_components
    (components_* kept for API compatibility; may be empty)
    """
    if not prompt or not prompt.strip():
        return {
            "over_engineered_score": 0.0,
            "improved_prompt": "",
            "over_engineered_explanation": "",
            "components_removed": [],
            "components_kept": [],
            "total_components": 0,
        }

    user_message = f"{AI_ANALYSIS_SYSTEM}\n\n---\n\nAnalyze this prompt:\n\n{prompt}"
    if user_input:
        user_message += "\n\nOptional context (sample input the prompt will process):\n"
        user_message += user_input

    try:
        data = call_model_json(user_message, api_key=api_key, max_tokens=1024)
    except Exception:
        # Fallback: use regular call and parse JSON from response
        full_prompt = f"{AI_ANALYSIS_SYSTEM}\n\n{user_message}\n\nRespond with valid JSON only."
        raw = call_model(
            full_prompt,
            api_key=api_key,
        )
        data = _parse_json_fallback(raw) if raw else {}

    simplified = (data.get("simplified_prompt") or "").strip()
    explanation = (data.get("over_engineered_explanation") or "").strip()
    score_raw = data.get("over_engineered_score")
    try:
        score = max(0.0, min(1.0, float(score_raw)))
    except (TypeError, ValueError):
        # Derive score from length reduction if AI didn't provide valid score
        orig_len = len(prompt)
        new_len = len(simplified) if simplified else orig_len
        score = 1.0 - (new_len / orig_len) if orig_len > 0 else 0.0
        score = max(0.0, min(1.0, score))

    improved = simplified if simplified else prompt

    return {
        "over_engineered_score": round(score, 2),
        "improved_prompt": improved,
        "over_engineered_explanation": explanation,
        "components_removed": [],
        "components_kept": [],
        "total_components": 0,
    }
