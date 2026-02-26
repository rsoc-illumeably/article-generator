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

    Records every call in self.calls / self.structured_calls for assertion.
    Returns self.response (for complete) or self.structured_response (for
    complete_structured), both of which can be set per test.

    If `responses` is provided, complete() pops from the front of that list
    on each invocation, falling back to self.response when the list is
    exhausted. This allows tests that need distinct return values per call
    (e.g. research text on call 1, article text on call 2) to control the
    sequence precisely without breaking tests that only set response.
    """

    def __init__(
        self,
        response: str = "mock response",
        responses: list[str] | None = None,
        structured_response: dict | None = None,
    ) -> None:
        self.response = response
        self._response_queue: list[str] = list(responses) if responses else []
        self.structured_response = (
            structured_response
            if structured_response is not None
            else {"verdict": "pass", "annotations": []}
        )
        self.calls: list[dict] = []
        self.structured_calls: list[dict] = []

    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools=None,
    ) -> str:
        self.calls.append(
            {"system_prompt": system_prompt, "messages": messages, "tools": tools}
        )
        return self._response_queue.pop(0) if self._response_queue else self.response

    def complete_structured(
        self,
        system_prompt: str,
        messages: list[dict],
        tool: dict,
    ) -> dict:
        self.structured_calls.append(
            {"system_prompt": system_prompt, "messages": messages, "tool": tool}
        )
        return self.structured_response


@pytest.fixture
def client(monkeypatch):
    """TestClient with API_KEY set in the environment.

    Simulates the server having a valid API_KEY configured — the same
    condition that always holds in a real deployment. Individual tests
    control whether they pass the key in the request header or not.
    """
    monkeypatch.setenv("API_KEY", TEST_API_KEY)
    return TestClient(app)
