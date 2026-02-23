"""API routes.

Exposes:
    POST /api/generate
        — Accepts a GenerateRequest (topic, verbose flag, optional dev_mode flag).
        — Validates input and delegates to the agent loop.
        — Returns a GenerateResponse (article + metadata, or error details).
        — Protected by the require_api_key dependency from auth.py.
"""

# TODO: implement
