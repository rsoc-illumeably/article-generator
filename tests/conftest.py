"""Shared pytest fixtures for the article-generator test suite."""

import pytest
from fastapi.testclient import TestClient

from src.main import app

# A fixed API key injected into the environment for every test.
# Mirrors how API_KEY would be set via .env in a real deployment.
TEST_API_KEY = "test-api-key-123"


@pytest.fixture
def client(monkeypatch):
    """TestClient with API_KEY set in the environment.

    Simulates the server having a valid API_KEY configured — the same
    condition that always holds in a real deployment. Individual tests
    control whether they pass the key in the request header or not.
    """
    monkeypatch.setenv("API_KEY", TEST_API_KEY)
    return TestClient(app)
