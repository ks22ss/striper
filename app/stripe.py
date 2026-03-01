"""Stripe method: strip prompt components and compare outputs to detect over-engineering."""

import os
import re

from app.openai_client import call_model, cosine_similarity, get_embedding

DEFAULT_SIMILARITY_THRESHOLD = 0.92


def _get_similarity_threshold() -> float:
    """Similarity threshold from env; above this, stripped output is deemed redundant."""
    raw = os.getenv("SIMILARITY_THRESHOLD", str(DEFAULT_SIMILARITY_THRESHOLD))
    try:
        val = float(raw)
        return max(0.0, min(1.0, val))
    except ValueError:
        return DEFAULT_SIMILARITY_THRESHOLD


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


def _test_removal_similarity(
    components: list[str],
    remove_index: int,
    active_indices: set[int],
    baseline_embedding: list[float],
    user_input: str | None = None,
    api_key: str | None = None,
) -> float:
    """
    Test removing component at *remove_index* from the current active set.
    Returns cosine similarity between the stripped output and the baseline.
    """
    remaining = sorted(active_indices - {remove_index})
    if not remaining:
        return 0.0
    stripped_prompt = " ".join(components[i] for i in remaining)
    stripped_full = _build_full_prompt(stripped_prompt, user_input)
    stripped_output = call_model(stripped_full, api_key=api_key)
    stripped_embedding = get_embedding(stripped_output, api_key=api_key)
    return cosine_similarity(baseline_embedding, stripped_embedding)


_LIST_MARKER_RE = re.compile(r"^\s*[-•*]|\s*\d+[.)]\s")


def parse_components(prompt: str) -> list[str]:
    """
    Parse prompt into components (sentences/clauses).
    Splits on newlines, then on sentence boundaries (. ! ?), filters empty.
    Lines that start with list markers (-, •, *, 1.) are kept as single units
    so that multi-sentence list items are not broken apart.
    """
    lines = [line.strip() for line in prompt.split("\n") if line.strip()]
    components: list[str] = []

    for line in lines:
        if _LIST_MARKER_RE.match(line):
            components.append(line)
        else:
            parts = re.split(r"(?<=[.!?])\s+", line)
            for part in parts:
                part = part.strip()
                if part:
                    components.append(part)

    if not components:
        components = [prompt.strip()] if prompt.strip() else []

    return components


def _validate_prompt(
    prompt_text: str,
    baseline_embedding: list[float],
    user_input: str | None = None,
    api_key: str | None = None,
) -> float:
    """Run a prompt through the model and return similarity to the baseline."""
    full = _build_full_prompt(prompt_text, user_input)
    output = call_model(full, api_key=api_key)
    emb = get_embedding(output, api_key=api_key)
    return cosine_similarity(baseline_embedding, emb)


def run_stripe_analysis(
    prompt: str,
    user_input: str | None = None,
    api_key: str | None = None,
) -> dict:
    """
    Run the Stripe method analysis.

    Uses a three-phase approach:
      1. Sequential cumulative removal (reverse order) — test each component's
         redundancy in the context of already-removed components, starting from
         the end (auxiliary/formatting components tend to appear last).
      2. Final validation — verify the improved prompt as a whole still produces
         output similar to the baseline.
      3. Greedy recovery — if validation fails, add back removed components
         front-first (core task components tend to appear first) until the
         improved prompt is valid again.

    Returns dict with over_engineered_score, improved_prompt,
    components_removed, components_kept.
    """
    components = parse_components(prompt)
    if not components:
        return _build_analysis_result(0.0, prompt, [], [], 0)

    full_prompt = _build_full_prompt(prompt, user_input)
    baseline_output = call_model(full_prompt, api_key=api_key)
    baseline_embedding = get_embedding(baseline_output, api_key=api_key)
    threshold = _get_similarity_threshold()

    # --- Phase 1: Sequential cumulative removal (reverse order) ---
    active_indices = set(range(len(components)))
    for i in reversed(range(len(components))):
        sim = _test_removal_similarity(
            components, i, active_indices, baseline_embedding, user_input, api_key
        )
        if sim >= threshold:
            active_indices.discard(i)

    # --- Phase 2: Validate the combined improved prompt ---
    redundant_indices = set(range(len(components))) - active_indices
    components_kept, components_removed = _classify_components(components, redundant_indices)
    improved_prompt = _build_improved_prompt(components_kept, prompt)

    validation_sim = _validate_prompt(improved_prompt, baseline_embedding, user_input, api_key)

    # --- Phase 3: Greedy recovery if validation failed ---
    if validation_sim < threshold and redundant_indices:
        for idx in sorted(redundant_indices):
            active_indices.add(idx)
            candidate_kept = [components[j] for j in sorted(active_indices)]
            candidate_prompt = " ".join(candidate_kept)
            validation_sim = _validate_prompt(
                candidate_prompt, baseline_embedding, user_input, api_key
            )
            if validation_sim >= threshold:
                break

        redundant_indices = set(range(len(components))) - active_indices
        components_kept, components_removed = _classify_components(components, redundant_indices)
        improved_prompt = _build_improved_prompt(components_kept, prompt)

    over_engineered_score = len(redundant_indices) / len(components) if components else 0.0
    return _build_analysis_result(
        over_engineered_score,
        improved_prompt,
        components_removed,
        components_kept,
        len(components),
    )
