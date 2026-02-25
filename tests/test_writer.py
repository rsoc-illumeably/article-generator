"""Tests for the Writer agent."""

from src.agents.writer import WriterAgent
from tests.conftest import MockLLMClient


def test_write_returns_llm_response():
    """Writer returns exactly what the LLM returns."""
    llm = MockLLMClient(response="The article content.")
    writer = WriterAgent(llm)
    result = writer.write(topic="The Roman Empire")
    assert result == "The article content."


def test_write_calls_complete_once():
    """Writer makes exactly one LLM call per write() invocation."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert len(llm.calls) == 1


def test_write_includes_topic_in_system_prompt():
    """The topic must appear in the system prompt."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert "The Roman Empire" in llm.calls[0]["system_prompt"]


def test_write_without_feedback_has_no_leftover_placeholder():
    """No raw {feedback} placeholder must remain in the prompt."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert "{feedback}" not in llm.calls[0]["system_prompt"]


def test_write_with_feedback_includes_annotations():
    """Annotations from the Judge must appear in the system prompt on revision."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(
        topic="The Roman Empire",
        feedback=["Claim about Caesar is unverified.", "Missing conclusion section."],
    )
    system_prompt = llm.calls[0]["system_prompt"]
    assert "Claim about Caesar is unverified." in system_prompt
    assert "Missing conclusion section." in system_prompt


def test_write_without_feedback_excludes_feedback_block():
    """When called without feedback, the prompt contains no feedback header."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert "Feedback from the previous review" not in llm.calls[0]["system_prompt"]


def test_write_system_prompt_includes_article_rules():
    """Article structure rules from config must be present in the system prompt."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    system_prompt = llm.calls[0]["system_prompt"]
    assert "Maximum word count" in system_prompt
    assert "Required sections" in system_prompt


def test_write_passes_no_tools():
    """Writer must not pass any tools to the LLM."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert llm.calls[0]["tools"] is None
