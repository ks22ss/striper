"""OpenAI API client for model calls and embeddings."""

import os

from openai import OpenAI

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        _client = OpenAI(api_key=api_key)
    return _client


def _resolve_client(api_key: str | None) -> OpenAI:
    """Use provided API key or fall back to env-configured client."""
    return OpenAI(api_key=api_key) if api_key else get_client()


def call_model(prompt: str, model: str = "gpt-4o-mini", api_key: str | None = None) -> str:
    """Call the model with a prompt and return the response text."""
    client = _resolve_client(api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond concisely to the user's prompt.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content or ""


def get_embedding(
    text: str, model: str = "text-embedding-3-small", api_key: str | None = None
) -> list[float]:
    """Get embedding vector for text."""
    client = _resolve_client(api_key)
    response = client.embeddings.create(
        model=model,
        input=text,
    )
    return response.data[0].embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
