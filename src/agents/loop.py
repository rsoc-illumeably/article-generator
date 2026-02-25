"""Agent loop orchestrator.

Drives the Writer → Judge iteration cycle:

    1. Writer produces an initial draft.
    2. Judge fact-checks the draft.
    3. If Judge passes  → return GenerateResponse.
    4. If Judge flags issues → pass annotations back to Writer → goto 2.
    5. If max_iterations reached without a pass → return ErrorResponse
       containing the full per-iteration reasoning chain.

Public entry point:
    run(topic, verbose, dev_mode) → GenerateResponse | ErrorResponse

Testable inner function:
    _execute(topic, verbose, dev_mode, writer, judge) → GenerateResponse | ErrorResponse
"""

from src.agents.judge import JudgeAgent
from src.agents.writer import WriterAgent
from src.config import get_config
from src.llm.factory import get_llm_client
from src.models.schemas import ErrorResponse, GenerateResponse, IterationRecord


def run(
    topic: str,
    verbose: bool,
    dev_mode: bool,
) -> GenerateResponse | ErrorResponse:
    """Build agents from the configured LLM client and run the loop.

    This is the public entry point called by the route handler. It handles
    instantiation only — all loop logic lives in _execute().
    """
    llm = get_llm_client()
    writer = WriterAgent(llm)
    judge = JudgeAgent(llm)
    return _execute(topic, verbose, dev_mode, writer, judge)


def _execute(
    topic: str,
    verbose: bool,
    dev_mode: bool,
    writer: WriterAgent,
    judge: JudgeAgent,
) -> GenerateResponse | ErrorResponse:
    """Run the Writer → Judge loop and return a structured response.

    Separated from run() so tests can inject mock agents directly without
    touching the LLM factory or real API calls.
    """
    max_iterations = get_config().agent.max_iterations
    history: list[IterationRecord] = []
    feedback: list[str] | None = None

    for iteration in range(1, max_iterations + 1):
        draft = writer.write(topic=topic, feedback=feedback)
        result = judge.judge(topic=topic, article=draft)

        history.append(
            IterationRecord(
                iteration=iteration,
                writer_output=draft,
                judge_verdict=result.verdict,
                judge_annotations=result.annotations,
            )
        )

        if result.verdict == "pass":
            return GenerateResponse(
                article=draft,
                iterations=iteration,
                history=history if (verbose or dev_mode) else None,
            )

        feedback = result.annotations

    return ErrorResponse(
        error=f"Article did not pass after {max_iterations} iterations.",
        iterations=max_iterations,
        history=history,
    )
