"""Stripe method: strip prompt components and compare outputs to detect over-engineering."""

import re
from app.openai_client import call_model, get_embedding, cosine_similarity

# Similarity threshold: if stripped output is this similar to baseline, component is redundant
SIMILARITY_THRESHOLD = 0.92


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

    # Execution task: we ask the model to "execute" the prompt as if it were instructions
    # and produce a sample response. This reveals which parts actually affect behavior.
    exec_task = (
        "Below are instructions for an AI assistant. "
        "Imagine you are that assistant. Produce a SHORT sample response (2-3 sentences) "
        "as you would reply to a user asking 'What can you help me with?' "
        "Follow the instructions exactly.\n\n---\n\n"
    )

    full_prompt = exec_task + prompt
    baseline_output = call_model(full_prompt)
    baseline_embedding = get_embedding(baseline_output)

    redundant_indices: set[int] = set()

    for i in range(len(components)):
        stripped_components = components[:i] + components[i + 1 :]
        stripped_prompt = " ".join(stripped_components)
        stripped_full = exec_task + stripped_prompt
        stripped_output = call_model(stripped_full)
        stripped_embedding = get_embedding(stripped_output)
        sim = cosine_similarity(baseline_embedding, stripped_embedding)
        if sim >= SIMILARITY_THRESHOLD:
            redundant_indices.add(i)

    components_kept = [c for i, c in enumerate(components) if i not in redundant_indices]
    components_removed = [c for i, c in enumerate(components) if i in redundant_indices]

    improved_prompt = " ".join(components_kept) if components_kept else prompt
    over_engineered_score = len(redundant_indices) / len(components) if components else 0.0

    return {
        "over_engineered_score": round(over_engineered_score, 2),
        "improved_prompt": improved_prompt,
        "components_removed": components_removed,
        "components_kept": components_kept,
        "total_components": len(components),
    }
