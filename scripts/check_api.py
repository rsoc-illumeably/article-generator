"""Live connectivity check for the configured LLM provider.

Run this manually from the project root to verify that your API key
is valid and the provider is reachable before deploying:

    python scripts/check_api.py

Reads the active provider and model from config/app.yml.
Loads credentials from .env if present.
Makes a single minimal API call and reports pass or fail.
"""

import sys
from pathlib import Path

# Allow imports from the project root (src.*, config.*).
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.config import get_config
from src.llm.anthropic_client import AnthropicClient


def check_anthropic() -> None:
    print("  Instantiating AnthropicClient...")
    client = AnthropicClient()
    print("  Sending minimal completion request...")
    response = client.complete(
        system_prompt="You are a test assistant.",
        messages=[{"role": "user", "content": "Reply with only the word OK."}],
    )
    print(f"  Response: {response!r}")
    if not response.strip():
        raise ValueError("Empty response received.")


PROVIDER_CHECKS = {
    "anthropic": check_anthropic,
}


def main() -> None:
    config = get_config()
    provider = config.llm.provider
    model = config.llm.model

    print(f"Provider : {provider}")
    print(f"Model    : {model}")
    print()

    check_fn = PROVIDER_CHECKS.get(provider)
    if check_fn is None:
        print(f"[FAIL] No connectivity check implemented for provider '{provider}'.")
        sys.exit(1)

    try:
        check_fn()
        print()
        print("[PASS] API call succeeded.")
    except KeyError as exc:
        print()
        print(f"[FAIL] Missing environment variable: {exc}")
        print("       Make sure your .env file is present and contains the required key.")
        sys.exit(1)
    except Exception as exc:
        print()
        print(f"[FAIL] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
