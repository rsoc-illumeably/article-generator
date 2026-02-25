"""Tests for the Judge agent."""

from src.agents.judge import VERDICT_TOOL, JudgeAgent
from src.llm.anthropic_client import WEB_SEARCH_TOOL
from tests.conftest import MockLLMClient


# --- Call 1: web search ---


def test_judge_passes_web_search_tool_on_first_call():
    """Call 1 must pass the web search tool to the LLM."""
    llm = MockLLMClient()
    judge = JudgeAgent(llm)
    judge.judge(topic="The Roman Empire", article="Some article text.")
    assert llm.calls[0]["tools"] == [WEB_SEARCH_TOOL]


def test_judge_includes_topic_in_system_prompt():
    """The topic must appear in the Judge's system prompt."""
    llm = MockLLMClient()
    judge = JudgeAgent(llm)
    judge.judge(topic="The Roman Empire", article="Some article text.")
    assert "The Roman Empire" in llm.calls[0]["system_prompt"]


def test_judge_includes_article_in_system_prompt():
    """The article draft must appear in the Judge's system prompt."""
    llm = MockLLMClient()
    judge = JudgeAgent(llm)
    judge.judge(topic="The Roman Empire", article="Some article text.")
    assert "Some article text." in llm.calls[0]["system_prompt"]


# --- Call 2: forced structured verdict ---


def test_judge_passes_verdict_tool_on_second_call():
    """Call 2 must pass the VERDICT_TOOL to complete_structured."""
    llm = MockLLMClient()
    judge = JudgeAgent(llm)
    judge.judge(topic="The Roman Empire", article="Some article text.")
    assert llm.structured_calls[0]["tool"] == VERDICT_TOOL


def test_judge_threads_research_into_verdict_call():
    """The research text from call 1 must appear in the messages for call 2."""
    llm = MockLLMClient(response="my research findings")
    judge = JudgeAgent(llm)
    judge.judge(topic="The Roman Empire", article="Some article text.")
    verdict_messages = llm.structured_calls[0]["messages"]
    assert any(
        m.get("role") == "assistant" and "my research findings" in m.get("content", "")
        for m in verdict_messages
    )


# --- JudgeResult construction ---


def test_judge_returns_pass_verdict():
    """A pass response from the tool call returns verdict='pass' with empty annotations."""
    llm = MockLLMClient(structured_response={"verdict": "pass", "annotations": []})
    judge = JudgeAgent(llm)
    result = judge.judge(topic="The Roman Empire", article="Some article text.")
    assert result.verdict == "pass"
    assert result.annotations == []


def test_judge_returns_fail_verdict_with_annotations():
    """A fail response returns verdict='fail' with the annotations list."""
    llm = MockLLMClient(
        structured_response={
            "verdict": "fail",
            "annotations": [
                "Claim about Caesar in paragraph 2 is unverified.",
                "Missing conclusion section.",
            ],
        }
    )
    judge = JudgeAgent(llm)
    result = judge.judge(topic="The Roman Empire", article="Some article text.")
    assert result.verdict == "fail"
    assert len(result.annotations) == 2
    assert "Claim about Caesar in paragraph 2 is unverified." in result.annotations
