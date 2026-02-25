"""FastAPI application factory.

Creates and configures the FastAPI app instance, loads all YAML config at
startup, and defines all routes via decorators. This is the entry point
referenced by uvicorn in the Dockerfile and compose files (src.main:app).

Routes:
    GET  /                    — browser UI (no auth)
    GET  /health              — liveness check (no auth)
    POST /api/generate        — submit a generation job; requires X-API-Key header;
                                returns a job_id immediately; loop runs in background
    GET  /api/status/{job_id} — poll job progress; requires X-API-Key header;
                                returns current phase, iteration, and final result
"""

import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import Depends, FastAPI, HTTPException

from src.agents.loop import run
from src.api.auth import require_api_key
from src.config import get_config
from src.frontend.routes import router as frontend_router
from src.models.schemas import GenerateRequest

app = FastAPI(
    title="article-generator",
    description="Personal article generation service using a Writer + Judge agent loop.",
)

app.include_router(frontend_router)

# Load and validate all YAML configs at startup.
# Any misconfigured YAML will raise here before the server accepts requests.
config = get_config()

# In-memory job store. Keys are UUIDs; values are mutable dicts written to by
# background threads and read by the /api/status endpoint.
# Cleared on container restart — by design.
jobs: dict[str, dict] = {}

# Thread pool for background generation jobs.
_executor = ThreadPoolExecutor(max_workers=4)


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
    """Submit an article generation job.

    Returns a job_id immediately. The Writer→Judge loop runs in a background
    thread and writes progress to the shared jobs dict. Poll GET /api/status
    to track progress and retrieve the final result.
    """
    job_id = str(uuid.uuid4())
    job: dict = {
        "status": "running",
        "iteration": 0,
        "max_iterations": config.agent.max_iterations,
        "phase": None,
        "last_verdict": None,
        "result": None,
        "error": None,
    }
    jobs[job_id] = job
    _executor.submit(run, request.topic, request.verbose, job)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def status(
    job_id: str,
    _: None = Depends(require_api_key),
) -> dict:
    """Return the current state of a generation job.

    While running: returns status, iteration, max_iterations, phase, last_verdict.
    When done:     also includes result (GenerateResponse fields).
    When error:    also includes error message and result (ErrorResponse fields).
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    return jobs[job_id]
