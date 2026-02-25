"""Judge agent.

Receives the Writer's draft and the original topic, fact-checks via web
search, and returns a structured verdict.

Two-call flow
─────────────
Call 1 — research:
    The model is given the web_search tool and told to verify every factual
    claim. It returns a text analysis of what it found.

Call 2 — verdict:
    The research text is appended to the conversation and the model is forced
    to call ``submit_verdict`` via tool_choice. The Anthropic API guarantees
    the response conforms to the tool's input_schema, so no text parsing is
    needed and malformed output is structurally impossible.
"""

from dataclasses import dataclass, field

from src.config import get_config
from src.llm.anthropic_client import WEB_SEARCH_TOOL  # Anthropic-specific tool def
from src.llm.interface import LLMInterface

VERDICT_TOOL: dict = {
    "name": "submit_verdict",
    "description": (
        "Submit the final fact-checking verdict after completing your research. "
        "Call this tool once you have verified all factual claims in the article."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["pass", "fail"],
                "description": (
                    "pass if every factual claim is accurate; "
                    "fail if one or more claims are incorrect or unverifiable"
                ),
            },
            "annotations": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "One entry per factual issue found. Each entry states what is "
                    "wrong and where it appears in the article. "
                    "Empty list when verdict is pass."
                ),
            },
        },
        "required": ["verdict", "annotations"],
    },
}


@dataclass
class JudgeResult:
    verdict: str                          # "pass" or "fail"
    annotations: list[str] = field(default_factory=list)


class JudgeAgent:

    def __init__(self, llm: LLMInterface) -> None:
        self._llm = llm
        self._judge_config = get_config().judge

    def judge(self, topic: str, article: str) -> JudgeResult:
        """Fact-check the article and return a structured verdict.

        Args:
            topic: The original article topic.
            article: The Writer's draft to review.

        Returns:
            JudgeResult with verdict ("pass" or "fail") and any annotations.
        """
        system_prompt = self._build_system_prompt(topic, article)

        # Call 1: let the model research using web search.
        research_messages = [{"role": "user", "content": "Review the article now."}]
        research = self._llm.complete(
            system_prompt=system_prompt,
            messages=research_messages,
            tools=[WEB_SEARCH_TOOL],
        )

        # Call 2: force a structured verdict based on the research.
        verdict_messages = research_messages + [
            {"role": "assistant", "content": research},
            {"role": "user", "content": "Submit your verdict now."},
        ]
        data = self._llm.complete_structured(
            system_prompt=system_prompt,
            messages=verdict_messages,
            tool=VERDICT_TOOL,
        )

        return JudgeResult(
            verdict=data["verdict"],
            annotations=[str(a) for a in (data.get("annotations") or [])],
        )

    def _build_system_prompt(self, topic: str, article: str) -> str:
        criteria_text = "\n".join(
            f"- {criterion}" for criterion in self._judge_config.acceptance_criteria
        )
        prompt = self._judge_config.system_prompt.format(topic=topic, article=article)
        return f"{prompt}\nAcceptance criteria:\n{criteria_text}"
