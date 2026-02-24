"""API key authentication dependency.

Provides require_api_key — a FastAPI dependency that validates the
X-API-Key request header against the API_KEY environment variable.

Usage:
    from src.api.auth import require_api_key
    from fastapi import Depends

    @app.post("/api/generate")
    def generate(request: ..., _: None = Depends(require_api_key)):
        ...
"""

import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException, status


def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> None:
    """Validate the X-API-Key request header.

    Returns None on success (the return value is intentionally unused by callers).
    Raises HTTP 401 if the header is absent or does not match API_KEY.

    secrets.compare_digest is used instead of == to prevent timing attacks —
    it runs in constant time regardless of where the strings diverge.
    """
    api_key = os.environ.get("API_KEY", "")

    # Treat a missing header and a wrong header identically — both are 401.
    # Don't give callers information about which case they hit.
    if not x_api_key or not api_key or not secrets.compare_digest(x_api_key, api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
