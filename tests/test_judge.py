"""Tests for the Judge agent."""

import pytest

from src.agents.judge import JudgeAgent, _parse_verdict
from src.llm.anthropic_client import WEB_SEARCH_TOOL
from tests.conftest import MockLLMClient

PASS_RESPONSE = "verdict: pass\nannotations: []"
FAIL_RESPONSE = (
    "verdict: fail\n"
    "annotations:\n"
    "  - Claim about Caesar in paragraph 2 is unverified.\n"
    "  - Missing conclusion section.\n"
)


# --- JudgeAgent integration (mock LLM) ---


def test_judge_calls_complete_with_web_search_tool():
    """Judge must pass the web search tool to the LLM."""
    llm = MockLLMClient(response=PASS_RESPONSE)
    judge = JudgeAgent(llm)
    judge.judge(topic="The Roman Empire", article="Some article text.")
    assert llm.calls[0]["tools"] == [WEB_SEARCH_TOOL]


def test_judge_includes_topic_in_system_prompt():
    """The topic must appear in the Judge's system prompt."""
    llm = MockLLMClient(response=PASS_RESPONSE)
    judge = JudgeAgent(llm)
    judge.judge(topic="The Roman Empire", article="Some article text.")
    assert "The Roman Empire" in llm.calls[0]["system_prompt"]


def test_judge_includes_article_in_system_prompt():
    """The article draft must appear in the Judge's system prompt."""
    llm = MockLLMClient(response=PASS_RESPONSE)
    judge = JudgeAgent(llm)
    judge.judge(topic="The Roman Empire", article="Some article text.")
    assert "Some article text." in llm.calls[0]["system_prompt"]


# --- _parse_verdict: valid responses ---


def test_parse_verdict_pass():
    """A valid pass response returns verdict='pass' with empty annotations."""
    result = _parse_verdict(PASS_RESPONSE)
    assert result.verdict == "pass"
    assert result.annotations == []


def test_parse_verdict_fail_with_annotations():
    """A valid fail response returns verdict='fail' with the annotations list."""
    result = _parse_verdict(FAIL_RESPONSE)
    assert result.verdict == "fail"
    assert len(result.annotations) == 2
    assert "Claim about Caesar in paragraph 2 is unverified." in result.annotations


# --- _parse_verdict: error cases ---


def test_parse_verdict_raises_on_malformed_yaml():
    """Malformed YAML must raise ValueError immediately."""
    with pytest.raises(ValueError, match="malformed YAML"):
        _parse_verdict("verdict: [unclosed bracket")


def test_parse_verdict_raises_on_non_mapping():
    """A YAML list (not a mapping) must raise ValueError."""
    with pytest.raises(ValueError, match="YAML mapping"):
        _parse_verdict("- item1\n- item2")


def test_parse_verdict_raises_on_missing_verdict_field():
    """A YAML mapping without a 'verdict' key must raise ValueError."""
    with pytest.raises(ValueError, match="missing required 'verdict'"):
        _parse_verdict("annotations: []")


def test_parse_verdict_raises_on_invalid_verdict_value():
    """A verdict value other than 'pass' or 'fail' must raise ValueError."""
    with pytest.raises(ValueError, match="must be 'pass' or 'fail'"):
        _parse_verdict("verdict: maybe\nannotations: []")


def test_parse_verdict_raises_on_non_list_annotations():
    """Annotations that are not a YAML list must raise ValueError."""
    with pytest.raises(ValueError, match="must be a YAML list"):
        _parse_verdict("verdict: fail\nannotations: not a list")
