"""Writer agent.

Receives a topic (and optionally Judge feedback from a previous iteration)
and produces a full article draft. Uses the WriterConfig prompt template
and article structure rules loaded from config/writer_prompt.yml.

On first call: generates an initial draft from the topic alone.
On subsequent calls: revises the previous draft addressing every Judge annotation.
"""

from src.config import get_config
from src.llm.interface import LLMInterface


class WriterAgent:

    def __init__(self, llm: LLMInterface) -> None:
        self._llm = llm
        self._writer_config = get_config().writer

    def write(self, topic: str, feedback: list[str] | None = None) -> str:
        """Generate or revise an article draft.

        Args:
            topic: The article topic.
            feedback: Judge annotations from the previous round, or None on
                      the first call.

        Returns:
            The full article draft as a plain text string.
        """
        system_prompt = self._build_system_prompt(topic, feedback)
        messages = [{"role": "user", "content": "Write the article now."}]
        return self._llm.complete(system_prompt=system_prompt, messages=messages)

    def _build_system_prompt(self, topic: str, feedback: list[str] | None) -> str:
        feedback_text = ""
        if feedback:
            lines = "\n".join(f"- {annotation}" for annotation in feedback)
            feedback_text = f"Feedback from the previous review:\n{lines}"

        rules = self._writer_config.article_rules
        rules_text = (
            "Article structure rules:\n"
            f"- Maximum word count: {rules.max_word_count}\n"
            f"- Maximum paragraph count: {rules.max_paragraph_count}\n"
            f"- Required sections (in order): {', '.join(rules.required_sections)}\n"
            f"- Tone: {rules.tone}"
        )

        prompt = self._writer_config.system_prompt.format(
            topic=topic, feedback=feedback_text
        )
        return f"{prompt}\n{rules_text}"
