"""Judge agent.

Receives the original topic and the Writer's full article draft.
Uses Claude's native web search tool to fact-check every claim.
Returns either a passing verdict or a list of specific annotations
describing what is wrong and where.

Uses the JudgeConfig prompt template and acceptance criteria loaded
from config/judge_prompt.yml.
"""

# TODO: implement
