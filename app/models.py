"""Pydantic schemas for API request/response."""

from pydantic import BaseModel, EmailStr, Field


class AnalyzeRequest(BaseModel):
    """Request body for prompt analysis."""

    prompt: str = Field(..., min_length=1, description="The prompt to analyze for over-engineering")


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


# Auth schemas
class UserCreate(BaseModel):
    """Request body for user registration."""

    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """User info in API responses."""

    id: int
    username: str
    email: str


class LoginRequest(BaseModel):
    """Request body for login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PromptHistoryItem(BaseModel):
    """Single prompt history record."""

    id: int
    prompt: str
    over_engineered_score: float
    improved_prompt: str
    created_at: str


class PromptHistoryResponse(BaseModel):
    """List of prompt history items."""

    items: list[PromptHistoryItem]
