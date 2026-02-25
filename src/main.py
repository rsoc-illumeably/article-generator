"""FastAPI application factory.

Creates and configures the FastAPI app instance, loads all YAML config at
startup, and defines all routes via decorators. This is the entry point
referenced by uvicorn in the Dockerfile and compose files (src.main:app).

Routes:
    GET  /health          — liveness check, no auth required
    POST /api/generate    — generate an article; requires X-API-Key header
"""

from fastapi import Depends, FastAPI

from src.agents.loop import run
from src.api.auth import require_api_key
from src.config import get_config
from src.models.schemas import GenerateRequest

app = FastAPI(
    title="article-generator",
    description="Personal article generation service using a Writer + Judge agent loop.",
)

# Load and validate all YAML configs at startup.
# Any misconfigured YAML will raise here before the server accepts requests.
config = get_config()


@app.get("/health")
def health() -> dict:
    """Liveness check.

    Confirms the server is running and that config loaded correctly.
    Returns a subset of config values so callers can verify the right
    settings are active. No authentication required.
    """
    return {
        "status": "ok",
        "provider": config.llm.provider,
        "model": config.llm.model,
        "max_iterations": config.agent.max_iterations,
    }


@app.post("/api/generate")
def generate(
    request: GenerateRequest,
    _: None = Depends(require_api_key),
) -> dict:
    """Generate a fact-checked article from a topic.

    Protected by X-API-Key header authentication.
    Accepts a GenerateRequest body (topic, verbose, dev_mode).
    Returns a GenerateResponse on success or ErrorResponse if the iteration
    cap is reached without the Judge passing the article.
    """
    result = run(
        topic=request.topic,
        verbose=request.verbose,
        dev_mode=request.dev_mode,
    )
    return result.model_dump()
