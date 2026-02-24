"""LLM client factory.

Returns the concrete LLM client configured in config/app.yml.

To add a new provider:
    1. Implement a subclass of LLMInterface in src/llm/<provider>_client.py.
    2. Add an elif branch below mapping the provider string to that class.
    3. Update config/app.yml provider field to the new string.
"""

from src.config import get_config
from src.llm.interface import LLMInterface


def get_llm_client() -> LLMInterface:
    """Instantiate and return the LLM client for the configured provider."""
    provider = get_config().llm.provider
    if provider == "anthropic":
        from src.llm.anthropic_client import AnthropicClient
        return AnthropicClient()
    raise ValueError(f"Unknown LLM provider: '{provider}'. Check config/app.yml.")
