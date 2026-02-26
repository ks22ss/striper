"""FastAPI application for Striper - prompt over-engineering analyzer."""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.models import AnalyzeRequest, AnalyzeResponse
from app.stripe import run_stripe_analysis

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
        result = run_stripe_analysis(request.prompt)
        return AnalyzeResponse(**result)
    except ValueError as e:
        if "OPENAI_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="OpenAI API key not configured")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
