"""OpenAI API client for model calls and embeddings.

Supports both OpenAI and OpenRouter. Set OPENROUTER_API_KEY to use OpenRouter;
otherwise OPENAI_API_KEY is used. See https://openrouter.ai/docs/guides/community/openai-sdk
"""

import os

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Get or create OpenAI client (OpenRouter if OPENROUTER_API_KEY set, else OpenAI)."""
    global _client
    if _client is None:
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        if openrouter_key:
            _client = OpenAI(
                api_key=openrouter_key,
                base_url=OPENROUTER_BASE_URL,
            )
        elif openai_key:
            _client = OpenAI(api_key=openai_key)
        else:
            raise ValueError("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
    return _client


def _resolve_client(api_key: str | None) -> OpenAI:
    """Use provided API key or fall back to env-configured client."""
    return OpenAI(api_key=api_key) if api_key else get_client()


def call_model(
    prompt: str,
    model: str = "stepfun/step-3.5-flash:free",
    api_key: str | None = None,
) -> str:
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
    text: str, model: str = "thenlper/gte-base", api_key: str | None = None
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
