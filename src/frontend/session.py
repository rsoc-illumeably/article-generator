"""In-memory session store for browser authentication.

Sessions are stored as a set of random IDs in process memory.
All sessions are cleared when the container restarts — by design.
No expiry: a session is valid until the container goes down.
"""

import secrets

_sessions: set[str] = set()


def create_session() -> str:
    """Generate a new session ID, store it, and return it."""
    session_id = secrets.token_urlsafe(32)
    _sessions.add(session_id)
    return session_id


def is_valid(session_id: str | None) -> bool:
    """Return True if the session ID is known and active."""
    return session_id is not None and session_id in _sessions


def delete_session(session_id: str) -> None:
    """Remove a session ID (logout)."""
    _sessions.discard(session_id)
