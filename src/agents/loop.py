"""Agent loop orchestrator.

Drives the Writer → Judge iteration cycle:

    1. Writer produces an initial draft.
    2. Judge fact-checks the draft.
    3. If Judge passes  → return GenerateResponse.
    4. If Judge flags issues → pass annotations back to Writer → goto 2.
    5. If max_iterations reached without a pass → return ErrorResponse
       containing the full per-iteration reasoning chain.

Public entry point:
    run(topic, verbose, job) → GenerateResponse | ErrorResponse

    The optional `job` dict is written to after every iteration so that a
    polling status endpoint can report live progress to the browser. When
    job is None (unit tests, direct calls) no status updates are written.

Testable inner function:
    _execute(topic, verbose, writer, judge, job) → GenerateResponse | ErrorResponse
"""

import time

from src.agents.judge import JudgeAgent
from src.agents.writer import WriterAgent
from src.config import get_config
from src.llm.factory import get_llm_client
from src.models.schemas import ErrorResponse, GenerateResponse, IterationRecord


def run(
    topic: str,
    verbose: bool,
    job: dict | None = None,
) -> GenerateResponse | ErrorResponse:
    """Build agents from the configured LLM client and run the loop.

    This is the public entry point called by the route handler. It handles
    instantiation only — all loop logic lives in _execute().

    Any exception is caught, written to job["status"] = "error", then re-raised
    so the background thread exits cleanly regardless of what went wrong.
    """
    try:
        llm = get_llm_client()
        writer = WriterAgent(llm)
        judge = JudgeAgent(llm)
        return _execute(topic, verbose, writer, judge, job)
    except Exception as exc:
        if job is not None:
            job["status"] = "error"
            job["error"] = f"Unexpected error: {exc}"
        raise


def _execute(
    topic: str,
    verbose: bool,
    writer: WriterAgent,
    judge: JudgeAgent,
    job: dict | None = None,
) -> GenerateResponse | ErrorResponse:
    """Run the Writer → Judge loop and return a structured response.

    Separated from run() so tests can inject mock agents directly without
    touching the LLM factory or real API calls.

    When `job` is provided, writes live status after every agent call so the
    polling endpoint always reflects the current phase and iteration count.
    """
    max_iterations = get_config().agent.max_iterations
    history: list[IterationRecord] = []
    feedback: list[str] | None = None

    for iteration in range(1, max_iterations + 1):
        iteration_start = time.monotonic()

        if job is not None:
            job["iteration"] = iteration
            job["phase"] = "writing"

        draft = writer.write(topic=topic, feedback=feedback)

        if job is not None:
            job["phase"] = "judging"

        result = judge.judge(topic=topic, article=draft)
        duration = time.monotonic() - iteration_start

        if job is not None:
            job["last_verdict"] = result.verdict

        history.append(
            IterationRecord(
                iteration=iteration,
                writer_output=draft,
                judge_verdict=result.verdict,
                judge_annotations=result.annotations,
                duration_seconds=round(duration, 1),
            )
        )

        if result.verdict == "pass":
            response = GenerateResponse(
                article=draft,
                iterations=iteration,
                history=history if verbose else None,
            )
            if job is not None:
                job["status"] = "done"
                job["result"] = response.model_dump()
            return response

        feedback = result.annotations

    error_response = ErrorResponse(
        error=f"Article did not pass after {max_iterations} iterations.",
        iterations=max_iterations,
        history=history,
    )
    if job is not None:
        job["status"] = "error"
        job["error"] = error_response.error
        job["result"] = error_response.model_dump()
    return error_response
