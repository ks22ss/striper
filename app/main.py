"""FastAPI application for Striper - prompt over-engineering analyzer."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import AuthenticationError

from app.auth import authenticate_user, create_access_token, get_current_user, hash_password
from app.database import (
    add_prompt_history,
    create_user,
    get_prompt_history,
    get_user_by_email,
    get_user_by_username,
    init_db,
)
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    LoginRequest,
    PromptHistoryItem,
    PromptHistoryResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.stripe import run_stripe_analysis


def _is_api_key_error(exc: Exception) -> bool:
    """Check if the exception is due to missing OpenAI API key."""
    return "OPENAI_API_KEY" in str(exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Striper",
    description="Analyze prompts for over-engineering using the Stripe method",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files (frontend)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the main UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Striper API. Use POST /analyze to analyze a prompt."}


@app.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    """Register a new user. Returns JWT token on success."""
    if get_user_by_username(data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    if get_user_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    password_hash = hash_password(data.password)
    user_id = create_user(data.username, data.email, password_hash)
    token = create_access_token(data={"sub": str(user_id)})
    user = {"id": user_id, "username": data.username, "email": data.email}
    return TokenResponse(access_token=token, user=UserResponse(**user))


@app.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Authenticate user and return JWT token."""
    user = authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(data={"sub": str(user["id"])})
    return TokenResponse(access_token=token, user=UserResponse(**user))


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze a prompt for over-engineering using the Stripe method.
    Requires authentication. Saves result to user's prompt history.
    """
    try:
        result = run_stripe_analysis(
            request.prompt,
            user_input=request.input,
            api_key=request.api_key,
        )
        add_prompt_history(
            user_id=current_user["id"],
            prompt=request.prompt,
            over_engineered_score=result["over_engineered_score"],
            improved_prompt=result["improved_prompt"],
        )
        return AnalyzeResponse(**result)
    except ValueError as e:
        if _is_api_key_error(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key not configured",
            )
        raise HTTPException(status_code=400, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


HISTORY_MAX_LIMIT = 100


def _clamp_history_limit(limit: int) -> int:
    """Clamp history limit to a safe range to prevent abuse."""
    return max(1, min(HISTORY_MAX_LIMIT, limit))


@app.get("/history", response_model=PromptHistoryResponse)
async def get_history(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
):
    """Return the current user's prompt analysis history."""
    rows = get_prompt_history(current_user["id"], limit=_clamp_history_limit(limit))
    items = [
        PromptHistoryItem(
            id=row["id"],
            prompt=row["prompt"],
            over_engineered_score=row["over_engineered_score"],
            improved_prompt=row["improved_prompt"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return PromptHistoryResponse(items=items)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
