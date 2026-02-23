"""Config loader.

Reads all YAML config files at startup and exposes them as typed dataclasses.
Every other module imports from here — nothing else reads YAML directly.

Dataclasses defined here:
    LLMConfig       — provider, model name, API base URL
    AgentConfig     — max iteration cap
    ArticleRules    — max words, max paragraphs, required sections, tone
    WriterConfig    — system prompt template + ArticleRules
    JudgeConfig     — system prompt template + acceptance criteria list
    AppConfig       — top-level container holding all of the above
"""

# TODO: implement
