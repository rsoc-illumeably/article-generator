"""Judge agent.

Receives the Writer's draft and the original topic, fact-checks via web search,
and returns a structured verdict.

The Judge's LLM response must be valid YAML with exactly this schema:

    verdict: pass          # or: fail
    annotations: []        # empty list on pass; specific issues on fail

A malformed response or schema violation raises ValueError immediately.
"""

from dataclasses import dataclass, field

import yaml

from src.config import get_config
from src.llm.anthropic_client import WEB_SEARCH_TOOL  # Anthropic-specific tool def
from src.llm.interface import LLMInterface


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

        Raises:
            ValueError: If the LLM response is not valid YAML or violates the schema.
        """
        system_prompt = self._build_system_prompt(topic, article)
        messages = [{"role": "user", "content": "Review the article now."}]
        response = self._llm.complete(
            system_prompt=system_prompt,
            messages=messages,
            tools=[WEB_SEARCH_TOOL],
        )
        return _parse_verdict(response)

    def _build_system_prompt(self, topic: str, article: str) -> str:
        criteria_text = "\n".join(
            f"- {criterion}" for criterion in self._judge_config.acceptance_criteria
        )
        prompt = self._judge_config.system_prompt.format(topic=topic, article=article)
        return f"{prompt}\nAcceptance criteria:\n{criteria_text}"


def _parse_verdict(response: str) -> JudgeResult:
    """Parse the Judge's YAML response into a JudgeResult.

    Raises:
        ValueError: On malformed YAML, missing verdict field, invalid verdict
                    value, or non-list annotations.
    """
    try:
        data = yaml.safe_load(response)
    except yaml.YAMLError as exc:
        raise ValueError(f"Judge returned malformed YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Judge response must be a YAML mapping, got {type(data).__name__}."
        )

    if "verdict" not in data:
        raise ValueError("Judge response is missing required 'verdict' field.")

    verdict = str(data["verdict"]).lower()
    if verdict not in ("pass", "fail"):
        raise ValueError(
            f"Judge verdict must be 'pass' or 'fail', got: {verdict!r}."
        )

    annotations = data.get("annotations") or []
    if not isinstance(annotations, list):
        raise ValueError(
            f"Judge 'annotations' must be a YAML list, got {type(annotations).__name__}."
        )

    return JudgeResult(verdict=verdict, annotations=[str(a) for a in annotations])
