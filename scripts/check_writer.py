"""Live functionality check for the Writer agent.

Verifies that the Writer agent:
  1. Produces a non-empty article draft from a topic alone.
  2. Produces a revised draft when given Judge feedback.

Run from the project root:

    python scripts/check_writer.py

Requires ANTHROPIC_API_KEY in .env.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.agents.writer import WriterAgent
from src.llm.anthropic_client import AnthropicClient

TOPIC = "The Wright Brothers and the first powered flight at Kitty Hawk"


def main() -> None:
    print(f"Topic : {TOPIC}")
    print()

    try:
        llm = AnthropicClient()
        writer = WriterAgent(llm)
    except KeyError as exc:
        print(f"[FAIL] Missing environment variable: {exc}")
        print("       Make sure your .env file is present and contains the required key.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 1: Initial draft — no feedback
    # ------------------------------------------------------------------
    print("Step 1: Initial draft (no feedback)")
    print("-" * 60)

    try:
        draft = writer.write(topic=TOPIC)
        if not draft.strip():
            raise ValueError("Writer returned an empty response.")
        print(draft)
        print()
        print(f"[OK] Draft received ({len(draft.split())} words)")
    except Exception as exc:
        print()
        print(f"[FAIL] {exc}")
        sys.exit(1)

    print()

    # ------------------------------------------------------------------
    # Step 2: Revision — with Judge feedback
    # ------------------------------------------------------------------
    print("Step 2: Revision with feedback")
    print("-" * 60)

    feedback = [
        "The introduction does not clearly state the date of the first flight.",
        "The conclusion is too brief and does not summarise the significance of the achievement.",
    ]
    print("Feedback passed to writer:")
    for annotation in feedback:
        print(f"  - {annotation}")
    print()

    try:
        revision = writer.write(topic=TOPIC, feedback=feedback)
        if not revision.strip():
            raise ValueError("Writer returned an empty response on revision.")
        print(revision)
        print()
        print(f"[OK] Revision received ({len(revision.split())} words)")
    except Exception as exc:
        print()
        print(f"[FAIL] {exc}")
        sys.exit(1)

    print()
    print("[PASS] Writer agent checks passed.")


if __name__ == "__main__":
    main()
