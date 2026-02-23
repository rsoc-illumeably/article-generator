"""API key authentication.

Provides a FastAPI dependency that validates the X-API-Key request header
against the API_KEY value loaded from the environment. Raises HTTP 401 if
the header is missing or does not match.
"""

# TODO: implement
