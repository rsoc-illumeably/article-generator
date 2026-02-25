"""Tests for X-API-Key authentication on POST /api/generate."""

from tests.conftest import TEST_API_KEY


def test_missing_key_returns_401(client):
    """A request with no X-API-Key header should be rejected with 401."""
    response = client.post("/api/generate", json={"topic": "test"})
    assert response.status_code == 401


def test_wrong_key_returns_401(client):
    """A request with an incorrect X-API-Key should be rejected with 401."""
    response = client.post(
        "/api/generate",
        json={"topic": "test"},
        headers={"X-API-Key": "not-the-right-key"},
    )
    assert response.status_code == 401


def test_correct_key_returns_200(client, monkeypatch):
    """A request with the correct X-API-Key should be accepted with 200.

    The executor is patched out so no background thread is spawned.
    The route returns a job_id immediately — this test is about auth only.
    """
    monkeypatch.setattr("src.main._executor.submit", lambda *args, **kwargs: None)
    response = client.post(
        "/api/generate",
        json={"topic": "test"},
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert response.status_code == 200
    assert "job_id" in response.json()


def test_401_response_includes_detail(client):
    """A 401 response should include a human-readable detail field."""
    response = client.post("/api/generate", json={"topic": "test"})
    assert "detail" in response.json()
