"""Shared pytest fixtures for the article-generator test suite."""

import pytest
from fastapi.testclient import TestClient

from src.llm.interface import LLMInterface
from src.main import app

# A fixed API key injected into the environment for every test.
# Mirrors how API_KEY would be set via .env in a real deployment.
TEST_API_KEY = "test-api-key-123"


class MockLLMClient(LLMInterface):
    """Minimal LLM stub for agent unit tests.

    Records every call in self.calls for assertion.
    Returns self.response, which can be set per test.
    """

    def __init__(self, response: str = "mock response") -> None:
        self.response = response
        self.calls: list[dict] = []

    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools=None,
    ) -> str:
        self.calls.append(
            {"system_prompt": system_prompt, "messages": messages, "tools": tools}
        )
        return self.response


@pytest.fixture
def client(monkeypatch):
    """TestClient with API_KEY set in the environment.

    Simulates the server having a valid API_KEY configured — the same
    condition that always holds in a real deployment. Individual tests
    control whether they pass the key in the request header or not.
    """
    monkeypatch.setenv("API_KEY", TEST_API_KEY)
    return TestClient(app)
