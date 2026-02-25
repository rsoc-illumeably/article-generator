"""Tests for GET /health."""


def test_health_returns_200(client):
    """Health endpoint should return 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client):
    """Health response must contain status, provider, model, and max_iterations."""
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "provider" in body
    assert "model" in body
    assert "max_iterations" in body
