"""Stripe method: strip prompt components and compare outputs to detect over-engineering."""

import re

from app.openai_client import call_model, cosine_similarity, get_embedding

# Similarity threshold: if stripped output is this similar to baseline, component is redundant
SIMILARITY_THRESHOLD = 0.92

# Wrapper for execution task: model produces a sample response as if following the instructions
EXECUTION_TASK_PROMPT = (
    "Below are instructions for an AI assistant. "
    "Imagine you are that assistant. Produce a SHORT sample response (2-3 sentences) "
    "as you would reply to a user asking 'What can you help me with?' "
    "Follow the instructions exactly.\n\n---\n\n"
)


def _build_full_prompt(prompt_text: str) -> str:
    """Prepend execution task wrapper to the given prompt."""
    return EXECUTION_TASK_PROMPT + prompt_text


def _classify_components(
    components: list[str], redundant_indices: set[int]
) -> tuple[list[str], list[str]]:
    """Split components into kept (essential) and removed (redundant)."""
    kept = [c for i, c in enumerate(components) if i not in redundant_indices]
    removed = [c for i, c in enumerate(components) if i in redundant_indices]
    return kept, removed


def _is_component_redundant(
    components: list[str], index: int, baseline_embedding: list[float]
) -> bool:
    """
    Check if removing the component at index yields output similar to baseline.
    Strips the component, calls model, compares embeddings.
    """
    stripped_components = components[:index] + components[index + 1 :]
    stripped_prompt = " ".join(stripped_components)
    stripped_full = _build_full_prompt(stripped_prompt)
    stripped_output = call_model(stripped_full)
    stripped_embedding = get_embedding(stripped_output)
    sim = cosine_similarity(baseline_embedding, stripped_embedding)
    return sim >= SIMILARITY_THRESHOLD


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


def run_stripe_analysis(prompt: str) -> dict:
    """
    Run the Stripe method analysis.
    Returns dict with over_engineered_score, improved_prompt, components_removed, components_kept.
    """
    components = parse_components(prompt)
    if not components:
        return {
            "over_engineered_score": 0.0,
            "improved_prompt": prompt,
            "components_removed": [],
            "components_kept": [],
            "total_components": 0,
        }

    full_prompt = _build_full_prompt(prompt)
    baseline_output = call_model(full_prompt)
    baseline_embedding = get_embedding(baseline_output)

    redundant_indices: set[int] = set()
    for i in range(len(components)):
        if _is_component_redundant(components, i, baseline_embedding):
            redundant_indices.add(i)

    components_kept, components_removed = _classify_components(components, redundant_indices)

    improved_prompt = " ".join(components_kept) if components_kept else prompt
    over_engineered_score = len(redundant_indices) / len(components) if components else 0.0

    return {
        "over_engineered_score": round(over_engineered_score, 2),
        "improved_prompt": improved_prompt,
        "components_removed": components_removed,
        "components_kept": components_kept,
        "total_components": len(components),
    }
