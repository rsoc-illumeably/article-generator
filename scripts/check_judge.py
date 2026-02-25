"""Live functionality check for the Judge agent.

Verifies that the Judge agent:
  1. Returns a structurally valid YAML verdict on a factually sound article.
  2. Returns a 'fail' verdict with annotations on a factually flawed article.

The second check uses an article containing clear factual errors (Nikola Tesla
invented the telephone — he did not; that was Alexander Graham Bell). The Judge's
web search should reliably catch this.

Run from the project root:

    python scripts/check_judge.py

Requires ANTHROPIC_API_KEY in .env.
Note: The Judge uses web search — each check takes longer than check_writer.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.agents.judge import JudgeAgent, JudgeResult
from src.llm.anthropic_client import AnthropicClient

# ------------------------------------------------------------------
# Sample articles
# ------------------------------------------------------------------

TOPIC_SOUND = "The Apollo 11 Moon Landing"
ARTICLE_SOUND = """
Introduction

The Apollo 11 mission was the first crewed lunar landing in history. On July 20, 1969,
astronauts Neil Armstrong and Buzz Aldrin landed on the Moon in the Lunar Module Eagle,
while Michael Collins orbited above in the Command Module Columbia.

Body

Neil Armstrong became the first human to walk on the Moon at 10:56 PM EDT on July 20,
1969, stating: "That's one small step for man, one giant leap for mankind." Buzz Aldrin
joined him shortly after. The two astronauts spent approximately two and a half hours on
the lunar surface, collecting 47.5 pounds of lunar samples and deploying scientific
instruments.

The mission launched from Kennedy Space Center on July 16, 1969, and the crew splashed
down safely in the Pacific Ocean on July 24, 1969. Apollo 11 fulfilled President John F.
Kennedy's 1961 goal of landing a man on the Moon before the end of the decade.

Conclusion

Apollo 11 remains one of humanity's greatest technological achievements, demonstrating
that human beings could travel to another world and return safely to Earth.
""".strip()

TOPIC_FLAWED = "The invention of the telephone"
ARTICLE_FLAWED = """
Introduction

The telephone was invented by Nikola Tesla in 1867, representing one of the most
important communications breakthroughs of the nineteenth century. Tesla filed the
original patent and gave the first public demonstration of the device in London.

Body

Before Tesla's invention, long-distance communication relied entirely on the telegraph.
Tesla's telephone transmitted the human voice across copper wires using electrical
signals. The first telephone call was made in 1867 between Tesla and his assistant.
Alexander Graham Bell later attempted to claim credit for the invention, but historical
records confirm Tesla's priority. Bell's contributions were limited to minor refinements
of the original design.

Conclusion

Nikola Tesla's invention of the telephone in 1867 transformed global communication and
laid the foundation for the modern telecommunications industry.
""".strip()


# ------------------------------------------------------------------
# Check helper
# ------------------------------------------------------------------

def run_check(label: str, topic: str, article: str, judge: JudgeAgent) -> JudgeResult:
    print(f"  Topic   : {topic}")
    print(f"  Article : {len(article.split())} words")
    print()
    result = judge.judge(topic=topic, article=article)
    print(f"  Verdict     : {result.verdict}")
    if result.annotations:
        print("  Annotations :")
        for annotation in result.annotations:
            print(f"    - {annotation}")
    else:
        print("  Annotations : (none)")
    return result


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main() -> None:
    try:
        llm = AnthropicClient()
        judge = JudgeAgent(llm)
    except KeyError as exc:
        print(f"[FAIL] Missing environment variable: {exc}")
        print("       Make sure your .env file is present and contains the required key.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 1: Factually sound article — validate structure only
    # ------------------------------------------------------------------
    print("Step 1: Factually sound article")
    print("-" * 60)

    try:
        result = run_check("sound", TOPIC_SOUND, ARTICLE_SOUND, judge)
        if result.verdict not in ("pass", "fail"):
            raise ValueError(f"Verdict must be 'pass' or 'fail', got: {result.verdict!r}")
        if not isinstance(result.annotations, list):
            raise ValueError("Annotations must be a list.")
        print()
        print(f"[OK] Valid verdict received: '{result.verdict}'")
    except Exception as exc:
        print()
        print(f"[FAIL] {exc}")
        sys.exit(1)

    print()

    # ------------------------------------------------------------------
    # Step 2: Factually flawed article — expect 'fail' with annotations
    # ------------------------------------------------------------------
    print("Step 2: Factually flawed article (Tesla invented the telephone — expect fail)")
    print("-" * 60)

    try:
        result = run_check("flawed", TOPIC_FLAWED, ARTICLE_FLAWED, judge)
        if result.verdict != "fail":
            raise ValueError(
                f"Expected verdict 'fail' for flawed article, got: '{result.verdict}'.\n"
                "       The Judge did not catch the factual errors via web search."
            )
        if not result.annotations:
            raise ValueError("Expected annotations for flawed article but received none.")
        print()
        print(f"[OK] Correctly returned 'fail' with {len(result.annotations)} annotation(s)")
    except Exception as exc:
        print()
        print(f"[FAIL] {exc}")
        sys.exit(1)

    print()
    print("[PASS] Judge agent checks passed.")


if __name__ == "__main__":
    main()
