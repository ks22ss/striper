"""Stripe method: strip prompt components and compare outputs to detect over-engineering."""

import os
import re

from app.openai_client import call_model, cosine_similarity, get_embedding


def _get_similarity_threshold() -> float:
    """Similarity threshold from env; above this, stripped output is deemed redundant."""
    raw = os.getenv("SIMILARITY_THRESHOLD", "0.92")
    try:
        val = float(raw)
        return max(0.0, min(1.0, val))
    except ValueError:
        return 0.92


# Wrapper for execution task: model produces a sample response as if following the instructions
EXECUTION_TASK_INTRO = (
    "Below are instructions for an AI assistant. "
    "Imagine you are that assistant. Produce a SHORT sample response (2-3 sentences) "
)
EXECUTION_TASK_DEFAULT_INPUT = "as you would reply to a user asking 'What can you help me with?' "
EXECUTION_TASK_OUTRO = "Follow the instructions exactly.\n\n---\n\n"


def _build_full_prompt(prompt_text: str, user_input: str | None = None) -> str:
    """Build full prompt with execution task wrapper and optional user input."""
    if user_input:
        task = (
            EXECUTION_TASK_INTRO
            + "The user has sent you the following input. Respond to it. "
            + EXECUTION_TASK_OUTRO
            + prompt_text
            + "\n\nUser input:\n"
            + user_input
        )
    else:
        task = (
            EXECUTION_TASK_INTRO + EXECUTION_TASK_DEFAULT_INPUT + EXECUTION_TASK_OUTRO + prompt_text
        )
    return task


def _build_analysis_result(
    over_engineered_score: float,
    improved_prompt: str,
    components_removed: list[str],
    components_kept: list[str],
    total_components: int,
) -> dict:
    """Build the analysis result dict with consistent structure and rounded score."""
    return {
        "over_engineered_score": round(over_engineered_score, 2),
        "improved_prompt": improved_prompt,
        "components_removed": components_removed,
        "components_kept": components_kept,
        "total_components": total_components,
    }


def _classify_components(
    components: list[str], redundant_indices: set[int]
) -> tuple[list[str], list[str]]:
    """Split components into kept (essential) and removed (redundant)."""
    kept = [c for i, c in enumerate(components) if i not in redundant_indices]
    removed = [c for i, c in enumerate(components) if i in redundant_indices]
    return kept, removed


def _build_improved_prompt(components_kept: list[str], fallback: str) -> str:
    """Join kept components into improved prompt, or return fallback if none kept."""
    return " ".join(components_kept) if components_kept else fallback


def _is_component_redundant(
    components: list[str],
    index: int,
    baseline_embedding: list[float],
    user_input: str | None = None,
    api_key: str | None = None,
) -> bool:
    """
    Check if removing the component at index yields output similar to baseline.
    Strips the component, calls model, compares embeddings.
    """
    stripped_components = components[:index] + components[index + 1 :]
    stripped_prompt = " ".join(stripped_components)
    stripped_full = _build_full_prompt(stripped_prompt, user_input)
    stripped_output = call_model(stripped_full, api_key=api_key)
    stripped_embedding = get_embedding(stripped_output, api_key=api_key)
    sim = cosine_similarity(baseline_embedding, stripped_embedding)
    return sim >= _get_similarity_threshold()


def parse_components(prompt: str) -> list[str]:
    """
    Parse prompt into components (sentences/clauses).
    Splits on newlines, then on sentence boundaries (. ! ?), filters empty.
    """
    # First split by newlines to preserve structure
    lines = [line.strip() for line in prompt.split("\n") if line.strip()]
    components: list[str] = []

    for line in lines:
        # Split each line by sentence-ending punctuation
        parts = re.split(r"(?<=[.!?])\s+", line)
        for part in parts:
            part = part.strip()
            if part:
                components.append(part)

    # If we got nothing (e.g. no periods), treat whole prompt as one component
    if not components:
        components = [prompt.strip()] if prompt.strip() else []

    return components


def run_stripe_analysis(
    prompt: str,
    user_input: str | None = None,
    api_key: str | None = None,
) -> dict:
    """
    Run the Stripe method analysis.
    Returns dict with over_engineered_score, improved_prompt, components_removed, components_kept.
    user_input: optional text that the prompt will process (e.g. sample user message).
    api_key: optional OpenAI API key; if not provided, OPENAI_API_KEY env var is used.
    """
    components = parse_components(prompt)
    if not components:
        return _build_analysis_result(0.0, prompt, [], [], 0)

    full_prompt = _build_full_prompt(prompt, user_input)
    baseline_output = call_model(full_prompt, api_key=api_key)
    baseline_embedding = get_embedding(baseline_output, api_key=api_key)

    redundant_indices: set[int] = set()
    for i in range(len(components)):
        if _is_component_redundant(
            components, i, baseline_embedding, user_input=user_input, api_key=api_key
        ):
            redundant_indices.add(i)

    components_kept, components_removed = _classify_components(components, redundant_indices)

    improved_prompt = _build_improved_prompt(components_kept, prompt)
    over_engineered_score = len(redundant_indices) / len(components) if components else 0.0

    return _build_analysis_result(
        over_engineered_score, improved_prompt, components_removed, components_kept, len(components)
    )
