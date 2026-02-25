"""Pydantic request and response schemas.

All data flowing in and out of the API is typed here. Nothing else defines
wire-format models — import from this module throughout the app.

Classes:
    GenerateRequest   — incoming payload for POST /api/generate
    IterationRecord   — per-iteration agent trace (writer output + judge verdict)
    GenerateResponse  — success response: final article + optional history
    ErrorResponse     — failure response when the iteration cap is hit
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    # The topic to write about. Populated from typed input or file upload contents.
    # Kept intentionally short — the UI enforces a ~15 word soft limit.
    topic: str = Field(..., description="Topic for the article (keep to ~15 words).")

    # When True, the response includes the full per-iteration history and reasoning.
    verbose: bool = Field(False, description="Include full iteration history in the response.")


class IterationRecord(BaseModel):
    # 1-based iteration counter.
    iteration: int

    # Full article draft produced by the Writer in this iteration.
    writer_output: str

    # "pass" if the Judge accepted the draft; "fail" otherwise.
    judge_verdict: str

    # Empty list on a passing verdict. On failure, each entry describes a specific
    # issue and its location in the article.
    judge_annotations: list[str] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    success: bool = True

    # The final Judge-approved article.
    article: str

    # Total number of Writer→Judge iterations that completed.
    iterations: int

    # Populated when verbose=True or dev_mode=True; omitted otherwise.
    history: Optional[list[IterationRecord]] = None


class ErrorResponse(BaseModel):
    success: bool = False

    # Human-readable reason generation failed (e.g. "iteration cap reached").
    error: str

    # Number of iterations that ran before hitting the cap.
    iterations: int

    # Always included on error so the caller can inspect the full reasoning chain.
    history: list[IterationRecord]
