"""Tests for the Writer agent.

The Writer uses a three-call flow per write() invocation:
  calls[0] — plan:   think about what to search for (no tools)
  calls[1] — search: execute planned queries (tools=[WEB_SEARCH_TOOL], max 2 uses)
  calls[2] — write:  article generation (no tools, research in system prompt)

All tests target the appropriate call index.
"""

from src.agents.writer import WriterAgent
from tests.conftest import MockLLMClient


def test_write_returns_article_from_write_call():
    """Writer returns the result of the write call (call 2), not the research."""
    llm = MockLLMClient(responses=["plan text", "research output", "The article content."])
    writer = WriterAgent(llm)
    result = writer.write(topic="The Roman Empire")
    assert result == "The article content."


def test_write_uses_three_llm_calls():
    """Writer makes exactly three LLM calls per write(): plan, search, write."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert len(llm.calls) == 3


def test_write_plan_call_has_no_tools():
    """Plan call (0) passes no tools — forces the model to think before searching."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert llm.calls[0]["tools"] is None


def test_write_search_call_uses_web_search_tool():
    """Search call (1) passes the web_search tool; write call (2) passes no tools."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert llm.calls[1]["tools"] is not None
    assert llm.calls[2]["tools"] is None


def test_write_plan_call_includes_topic():
    """The topic appears in the plan call's user message."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert "The Roman Empire" in llm.calls[0]["messages"][0]["content"]


def test_write_plan_output_threaded_into_search_call():
    """Plan output from call 0 is passed as assistant context to call 1."""
    llm = MockLLMClient(responses=["unique plan text xyz", "research", "article"])
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    search_messages = llm.calls[1]["messages"]
    assert any(
        m.get("role") == "assistant" and "unique plan text xyz" in m.get("content", "")
        for m in search_messages
    )


def test_write_research_output_in_write_system_prompt():
    """Research output from call 1 is injected into call 2's system prompt."""
    llm = MockLLMClient(responses=["plan text", "unique research text xyz", "article"])
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert "unique research text xyz" in llm.calls[2]["system_prompt"]


def test_write_includes_topic_in_write_system_prompt():
    """The topic appears in the write call system prompt."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert "The Roman Empire" in llm.calls[2]["system_prompt"]


def test_write_without_feedback_has_no_leftover_placeholder():
    """No raw {feedback} placeholder remains in the write call system prompt."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert "{feedback}" not in llm.calls[2]["system_prompt"]


def test_write_with_feedback_includes_annotations_in_write_prompt():
    """Judge annotations appear in the write call system prompt on revision."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(
        topic="The Roman Empire",
        feedback=["Claim about Caesar is unverified.", "Missing conclusion section."],
    )
    system_prompt = llm.calls[2]["system_prompt"]
    assert "Claim about Caesar is unverified." in system_prompt
    assert "Missing conclusion section." in system_prompt


def test_write_with_feedback_includes_annotations_in_plan_query():
    """On revision, the plan query includes the Judge's annotations so the
    model can plan searches targeting the specific corrections needed."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(
        topic="The Roman Empire",
        feedback=["Claim about Caesar is unverified."],
    )
    plan_content = llm.calls[0]["messages"][0]["content"]
    assert "Claim about Caesar is unverified." in plan_content


def test_write_without_feedback_excludes_feedback_block_from_write_prompt():
    """When called without feedback, no feedback header appears in the write prompt."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    assert "Feedback from the previous review" not in llm.calls[2]["system_prompt"]


def test_write_system_prompt_includes_article_rules():
    """Article structure rules from config are present in the write call system prompt."""
    llm = MockLLMClient()
    writer = WriterAgent(llm)
    writer.write(topic="The Roman Empire")
    system_prompt = llm.calls[2]["system_prompt"]
    assert "Maximum word count" in system_prompt
    assert "Required sections" in system_prompt
