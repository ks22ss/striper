"""FastAPI application for Striper - prompt over-engineering analyzer."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import AnalyzeRequest, AnalyzeResponse
from app.stripe import run_stripe_analysis


def _is_api_key_error(exc: Exception) -> bool:
    """Check if the exception is due to missing OpenAI API key."""
    return "OPENAI_API_KEY" in str(exc)


app = FastAPI(
    title="Striper",
    description="Analyze prompts for over-engineering using the Stripe method",
    version="0.1.0",
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


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Analyze a prompt for over-engineering using the Stripe method.
    Returns over-engineered score, improved prompt, and component breakdown.
    """
    try:
        result = run_stripe_analysis(request.prompt, api_key=request.api_key)
        return AnalyzeResponse(**result)
    except ValueError as e:
        if _is_api_key_error(e):
            raise HTTPException(status_code=503, detail="OpenAI API key not configured")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
