"""Config loader.

Reads all YAML config files at startup and exposes them as typed dataclasses.
Every other module imports from here — nothing else reads YAML directly.

Dataclasses:
    LLMConfig       — provider, model name, API base URL
    AgentConfig     — max iteration cap
    ArticleRules    — max words, max paragraphs, required sections, tone
    WriterConfig    — system prompt template + ArticleRules
    JudgeConfig     — system prompt template + acceptance criteria list
    AppConfig       — top-level container holding all of the above
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

# Config directory is always at <project_root>/config/.
# This file lives at <project_root>/src/config.py, so go up one level.
_CONFIG_DIR = Path(__file__).parent.parent / "config"


@dataclass
class LLMConfig:
    provider: str      # e.g. "anthropic"
    model: str         # e.g. "claude-sonnet-4-6"
    api_base_url: str  # empty string means use the provider default


@dataclass
class AgentConfig:
    max_iterations: int  # loop cap before returning an error response


@dataclass
class ArticleRules:
    max_word_count: int
    max_paragraph_count: int
    required_sections: list[str]
    tone: str


@dataclass
class WriterConfig:
    # Prompt template — {topic} and {feedback} are injected by the agent loop at runtime.
    system_prompt: str
    article_rules: ArticleRules


@dataclass
class JudgeConfig:
    # Prompt template — {topic} and {article} are injected by the agent loop at runtime.
    system_prompt: str
    acceptance_criteria: list[str]


@dataclass
class AppConfig:
    llm: LLMConfig
    agent: AgentConfig
    writer: WriterConfig
    judge: JudgeConfig


def _load_yaml(filename: str) -> dict:
    """Read a single YAML file from the config directory and return it as a dict."""
    path = _CONFIG_DIR / filename
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _load_app_config() -> AppConfig:
    """Parse all YAML config files and assemble the full AppConfig dataclass tree."""
    app = _load_yaml("app.yml")
    writer = _load_yaml("writer_prompt.yml")
    judge = _load_yaml("judge_prompt.yml")

    return AppConfig(
        llm=LLMConfig(
            provider=app["llm"]["provider"],
            model=app["llm"]["model"],
            api_base_url=app["llm"]["api_base_url"],
        ),
        agent=AgentConfig(
            max_iterations=app["agent"]["max_iterations"],
        ),
        writer=WriterConfig(
            system_prompt=writer["system_prompt"],
            article_rules=ArticleRules(
                max_word_count=writer["article_rules"]["max_word_count"],
                max_paragraph_count=writer["article_rules"]["max_paragraph_count"],
                required_sections=writer["article_rules"]["required_sections"],
                tone=writer["article_rules"]["tone"],
            ),
        ),
        judge=JudgeConfig(
            system_prompt=judge["system_prompt"],
            acceptance_criteria=judge["acceptance_criteria"],
        ),
    )


# Module-level singleton — loaded once on first access, reused for every request.
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Return the loaded AppConfig, initialising it on first call."""
    global _config
    if _config is None:
        _config = _load_app_config()
    return _config
