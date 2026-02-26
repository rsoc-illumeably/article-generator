"""Tests for the Writer→Judge loop (_execute).

All tests use MockWriterAgent and MockJudgeAgent — no real LLM calls,
no real WriterAgent or JudgeAgent instantiation. This isolates the loop
logic (iteration control, feedback threading, response assembly) from
the agents themselves.

MockWriterAgent and MockJudgeAgent maintain response queues consumed
in call order. Each call is recorded in self.calls for assertions.
"""

from src.agents.judge import JudgeResult
from src.agents.loop import _execute
from src.config import get_config
from src.models.schemas import ErrorResponse, GenerateResponse


# ---------------------------------------------------------------------------
# Mock agents
# ---------------------------------------------------------------------------


class MockWriterAgent:
    """Stub WriterAgent that returns responses from a pre-set queue."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def write(self, topic: str, feedback: list[str] | None = None, on_phase=None) -> str:
        self.calls.append({"topic": topic, "feedback": feedback})
        return self._responses.pop(0)


class MockJudgeAgent:
    """Stub JudgeAgent that returns JudgeResults from a pre-set queue."""

    def __init__(self, results: list[JudgeResult]) -> None:
        self._results = list(results)
        self.calls: list[dict] = []

    def judge(self, topic: str, article: str, on_phase=None) -> JudgeResult:
        self.calls.append({"topic": topic, "article": article})
        return self._results.pop(0)


# Read max_iterations from config once for all cap-related tests.
MAX_ITER = get_config().agent.max_iterations


# ---------------------------------------------------------------------------
# Termination conditions
# ---------------------------------------------------------------------------


def test_pass_on_first_iteration():
    """Loop returns GenerateResponse immediately when judge passes on iteration 1."""
    writer = MockWriterAgent(["draft 1"])
    judge = MockJudgeAgent([JudgeResult("pass", [])])
    result = _execute("The Roman Empire", False, writer, judge)
    assert isinstance(result, GenerateResponse)
    assert result.success is True
    assert result.article == "draft 1"
    assert result.iterations == 1


def test_pass_on_second_iteration():
    """Loop iterates correctly: judge fails once then passes, iterations=2."""
    writer = MockWriterAgent(["draft 1", "draft 2"])
    judge = MockJudgeAgent([
        JudgeResult("fail", ["Claim X is unverified."]),
        JudgeResult("pass", []),
    ])
    result = _execute("The Roman Empire", False, writer, judge)
    assert isinstance(result, GenerateResponse)
    assert result.article == "draft 2"
    assert result.iterations == 2


def test_error_after_max_iterations():
    """Loop returns ErrorResponse when judge never passes within the iteration cap."""
    writer = MockWriterAgent([f"draft {i}" for i in range(1, MAX_ITER + 1)])
    judge = MockJudgeAgent([JudgeResult("fail", ["issue"]) for _ in range(MAX_ITER)])
    result = _execute("The Roman Empire", False, writer, judge)
    assert isinstance(result, ErrorResponse)
    assert result.success is False
    assert result.iterations == MAX_ITER
    assert str(MAX_ITER) in result.error


# ---------------------------------------------------------------------------
# Feedback and annotation threading
# ---------------------------------------------------------------------------


def test_first_writer_call_has_no_feedback():
    """Writer receives feedback=None on the first iteration — no prior judge output exists."""
    writer = MockWriterAgent(["draft 1"])
    judge = MockJudgeAgent([JudgeResult("pass", [])])
    _execute("The Roman Empire", False, writer, judge)
    assert writer.calls[0]["feedback"] is None


def test_annotations_threaded_to_next_writer_call():
    """Judge annotations from a failing verdict are passed as feedback to the next writer call."""
    writer = MockWriterAgent(["draft 1", "draft 2"])
    judge = MockJudgeAgent([
        JudgeResult("fail", ["Claim X is wrong.", "Missing conclusion section."]),
        JudgeResult("pass", []),
    ])
    _execute("The Roman Empire", False, writer, judge)
    assert writer.calls[1]["feedback"] == ["Claim X is wrong.", "Missing conclusion section."]


def test_feedback_updates_each_iteration():
    """Feedback is replaced each round — writer always receives only the latest annotations."""
    writer = MockWriterAgent(["draft 1", "draft 2", "draft 3"])
    judge = MockJudgeAgent([
        JudgeResult("fail", ["issue from round 1"]),
        JudgeResult("fail", ["issue from round 2"]),
        JudgeResult("pass", []),
    ])
    _execute("The Roman Empire", False, writer, judge)
    assert writer.calls[1]["feedback"] == ["issue from round 1"]
    assert writer.calls[2]["feedback"] == ["issue from round 2"]


# ---------------------------------------------------------------------------
# Data flow between agents
# ---------------------------------------------------------------------------


def test_draft_flows_from_writer_to_judge():
    """The exact string returned by writer becomes the article passed to judge."""
    writer = MockWriterAgent(["first draft", "second draft"])
    judge = MockJudgeAgent([
        JudgeResult("fail", ["issue"]),
        JudgeResult("pass", []),
    ])
    _execute("The Roman Empire", False, writer, judge)
    assert judge.calls[0]["article"] == "first draft"
    assert judge.calls[1]["article"] == "second draft"


# ---------------------------------------------------------------------------
# History and verbose flag
# ---------------------------------------------------------------------------


def test_verbose_false_omits_history_on_success():
    """GenerateResponse.history is None when verbose=False."""
    writer = MockWriterAgent(["draft 1"])
    judge = MockJudgeAgent([JudgeResult("pass", [])])
    result = _execute("The Roman Empire", False, writer, judge)
    assert result.history is None


def test_verbose_true_populates_history_on_success():
    """GenerateResponse.history is populated when verbose=True."""
    writer = MockWriterAgent(["draft 1"])
    judge = MockJudgeAgent([JudgeResult("pass", [])])
    result = _execute("The Roman Empire", True, writer, judge)
    assert result.history is not None
    assert len(result.history) == 1


def test_error_always_includes_history_regardless_of_verbose():
    """ErrorResponse.history is always populated even when verbose=False."""
    writer = MockWriterAgent([f"draft {i}" for i in range(1, MAX_ITER + 1)])
    judge = MockJudgeAgent([JudgeResult("fail", ["issue"]) for _ in range(MAX_ITER)])
    result = _execute("The Roman Empire", False, writer, judge)
    assert isinstance(result, ErrorResponse)
    assert result.history is not None
    assert len(result.history) == MAX_ITER


# ---------------------------------------------------------------------------
# IterationRecord fidelity
# ---------------------------------------------------------------------------


def test_iteration_records_contain_correct_agent_outputs():
    """Each IterationRecord captures the correct writer output, verdict, and annotations."""
    writer = MockWriterAgent(["draft 1", "draft 2"])
    judge = MockJudgeAgent([
        JudgeResult("fail", ["Claim X is wrong."]),
        JudgeResult("pass", []),
    ])
    result = _execute("The Roman Empire", True, writer, judge)

    first = result.history[0]
    assert first.iteration == 1
    assert first.writer_output == "draft 1"
    assert first.judge_verdict == "fail"
    assert first.judge_annotations == ["Claim X is wrong."]

    second = result.history[1]
    assert second.iteration == 2
    assert second.writer_output == "draft 2"
    assert second.judge_verdict == "pass"
    assert second.judge_annotations == []
