"""Frontend session management.

Manages a simple in-memory session store for browser-based authentication.
A session is created when the user enters the correct FRONTEND_SESSION_PASSWORD.
Sessions persist until the server restarts (no persistence required — this is
a personal, single-user tool).

Functions:
    create_session()  — generates a session token and stores it
    is_valid_session(token) — returns True if the token is in the store
    delete_session(token)   — removes a session (logout)
"""

# TODO: implement
