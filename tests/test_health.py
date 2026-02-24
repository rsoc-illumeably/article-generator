"""Tests for GET /health."""


def test_health_returns_200(client):
    """Health endpoint should return 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_requires_no_auth(client):
    """Health endpoint should be reachable without an X-API-Key header."""
    # Deliberately omit the API key header — health must remain publicly accessible.
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client):
    """Health response must contain status, provider, model, and max_iterations."""
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "provider" in body
    assert "model" in body
    assert "max_iterations" in body


def test_health_config_values(client):
    """Health response values should reflect what is set in config/app.yml."""
    body = client.get("/health").json()
    # These assertions will catch unintentional changes to the config defaults.
    assert body["provider"] == "anthropic"
    assert body["model"] == "claude-sonnet-4-6"
    assert isinstance(body["max_iterations"], int)
    assert body["max_iterations"] > 0
