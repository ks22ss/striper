"""Pydantic schemas for API request/response."""

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    """Request body for prompt analysis."""

    prompt: str = Field(..., min_length=1, description="The prompt to analyze for over-engineering")
    api_key: str | None = Field(
        default=None,
        description="Optional OpenAI API key. If not provided, OPENAI_API_KEY env var is used.",
    )

    @field_validator("api_key", mode="before")
    @classmethod
    def empty_api_key_to_none(cls, v: str | None) -> str | None:
        """Treat empty or whitespace-only api_key as None."""
        if v is None:
            return None
        return v.strip() or None


class AnalyzeResponse(BaseModel):
    """Response from prompt analysis."""

    over_engineered_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Score 0-1: higher = more over-engineered (more redundant components)",
    )
    improved_prompt: str = Field(..., description="Optimized prompt with redundant parts removed")
    components_removed: list[str] = Field(
        default_factory=list,
        description="Components deemed redundant and removed",
    )
    components_kept: list[str] = Field(
        default_factory=list,
        description="Components deemed essential and kept",
    )
    total_components: int = Field(..., description="Total number of components parsed from prompt")
