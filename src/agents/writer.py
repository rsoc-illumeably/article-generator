"""Writer agent.

Receives a topic (and optionally Judge feedback from a previous iteration)
and produces a full article draft. Uses a three-call flow:

  Call 1 (plan):   No tools. Model thinks about the article it needs to write
                   and outputs 1-2 precise search queries targeting the facts
                   most likely to require current, accurate data.

  Call 2 (search): Plan is passed as conversation context. Model executes the
                   planned queries via the web_search tool (capped at 2 uses)
                   and returns a research summary.

  Call 3 (write):  Research summary is injected into the system prompt as the
                   sole factual foundation. Model writes the article.

On revision rounds the plan query is targeted at the specific claims the
Judge flagged so the Writer searches for the correct information rather than
guessing at corrections.
"""

from src.config import get_config
from src.llm.anthropic_client import WEB_SEARCH_TOOL
from src.llm.interface import LLMInterface

# Instructs the model to think before searching — output is a numbered list
# of 1-2 concrete search queries, nothing else.
_PLAN_SYSTEM_PROMPT = (
    "You are a research planner preparing to write a factual article. "
    "Think carefully about what the article should cover and what specific facts "
    "need to be verified — focus on details likely to require current data: "
    "statistics, names of key figures, recent events, and exact dates. "
    "Output a numbered list of 1-2 precise search queries that will give the "
    "article writer the most important current facts. Nothing else."
)

# Instructs the model to execute the planned queries and summarise findings.
_SEARCH_SYSTEM_PROMPT = (
    "You are a research assistant executing a search plan for an article writer. "
    "Use the web_search tool to execute the planned queries and summarise the key "
    "facts you find. The article writer will rely on this summary as their sole "
    "factual foundation — be thorough and accurate."
)

# Web search tool capped at 2 uses so research stays targeted and fast.
_WEB_SEARCH_TOOL_2: dict = {**WEB_SEARCH_TOOL, "max_uses": 2}


class WriterAgent:

    def __init__(self, llm: LLMInterface) -> None:
        self._llm = llm
        self._writer_config = get_config().writer

    def write(
        self,
        topic: str,
        feedback: list[str] | None = None,
        on_phase: object = None,
    ) -> str:
        """Generate or revise an article draft.

        Three-call flow:
            Call 1 (plan):   think about what to search for (no tools).
            Call 2 (search): execute planned queries, max 2 web searches.
            Call 3 (write):  write the article grounded in the research.

        Args:
            topic: The article topic.
            feedback: Judge annotations from the previous round, or None on
                      the first call.
            on_phase: Optional callable(phase: str) invoked before each
                      sub-step so the caller can track granular progress.

        Returns:
            The full article draft as a plain text string.
        """
        if on_phase:
            on_phase("writer_researching")
        research = self._research(topic, feedback)

        if on_phase:
            on_phase("writer_drafting")
        return self._write(topic, feedback, research)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _research(self, topic: str, feedback: list[str] | None) -> str:
        """Two-sub-call research: plan what to search, then search."""
        plan_query = self._build_plan_query(topic, feedback)

        # Sub-call 1: plan (no tools — forces thinking before searching).
        plan = self._llm.complete(
            system_prompt=_PLAN_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": plan_query}],
        )

        # Sub-call 2: search — plan threaded in as assistant context.
        search_messages = [
            {"role": "user", "content": plan_query},
            {"role": "assistant", "content": plan},
            {"role": "user", "content": "Execute those searches now and summarise what you find."},
        ]
        return self._llm.complete(
            system_prompt=_SEARCH_SYSTEM_PROMPT,
            messages=search_messages,
            tools=[_WEB_SEARCH_TOOL_2],
        )

    def _build_plan_query(self, topic: str, feedback: list[str] | None) -> str:
        if feedback:
            issues = "\n".join(f"- {a}" for a in feedback)
            return (
                f"Article topic: {topic}\n\n"
                f"The previous draft was rejected for these factual errors:\n{issues}\n\n"
                f"What 1-2 searches will find the correct information to fix these issues?"
            )
        return (
            f"Article topic: {topic}\n\n"
            f"What 1-2 searches will give the most important current facts for this article?"
        )

    def _write(self, topic: str, feedback: list[str] | None, research: str) -> str:
        system_prompt = self._build_system_prompt(topic, feedback, research)
        messages = [{"role": "user", "content": "Write the article now."}]
        return self._llm.complete(system_prompt=system_prompt, messages=messages)

    def _build_system_prompt(
        self, topic: str, feedback: list[str] | None, research: str
    ) -> str:
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
        return (
            f"{prompt}\n\n"
            f"Research findings — use these as your sole factual foundation. "
            f"Do not state facts not supported by this research:\n{research}\n\n"
            f"{rules_text}"
        )
