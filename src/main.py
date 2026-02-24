"""FastAPI application factory.

Creates and configures the FastAPI app instance, loads all YAML config at
startup, and registers routers. This module is referenced by uvicorn as the
entry point in both the Dockerfile and the compose files (src.main:app).
"""

from fastapi import FastAPI

from src.config import get_config

app = FastAPI(
    title="article-generator",
    description="Personal article generation service using a Writer + Judge agent loop.",
)

# Load and validate all YAML configs at startup.
# Any missing key or bad YAML will raise immediately, before the server
# begins accepting requests — fail fast rather than fail on first request.
config = get_config()


@app.get("/health")
def health() -> dict:
    """Liveness check.

    Confirms the server is running and that config loaded correctly.
    Returns a subset of config values so callers can verify the right
    settings are active.
    """
    return {
        "status": "ok",
        "provider": config.llm.provider,
        "model": config.llm.model,
        "max_iterations": config.agent.max_iterations,
    }
