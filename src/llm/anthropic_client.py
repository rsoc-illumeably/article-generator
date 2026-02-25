"""Anthropic LLM client.

Concrete implementation of the LLM interface using the Anthropic SDK.
Wires up Claude's native web_search tool for use by the Judge agent.

Reads the model name and API base URL from AppConfig (config/app.yml).
Reads the ANTHROPIC_API_KEY from the environment.
"""

import os

import anthropic

from src.config import get_config
from src.llm.interface import LLMInterface

WEB_SEARCH_TOOL: dict = {"type": "web_search_20250305", "name": "web_search"}


class AnthropicClient(LLMInterface):

    def __init__(self) -> None:
        config = get_config().llm
        self._model = config.model
        kwargs = {"api_key": os.environ["ANTHROPIC_API_KEY"]}
        if config.api_base_url:
            kwargs["base_url"] = config.api_base_url
        self._client = anthropic.Anthropic(**kwargs)

    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools=None,
    ) -> str:
        kwargs = {
            "model": self._model,
            "system": system_prompt,
            "messages": messages,
            "max_tokens": 4096,
        }
        if tools is not None:
            kwargs["tools"] = tools
        response = self._client.messages.create(**kwargs)
        text_blocks = [block for block in response.content if block.type == "text"]
        return text_blocks[-1].text

    def complete_structured(
        self,
        system_prompt: str,
        messages: list[dict],
        tool: dict,
    ) -> dict:
        response = self._client.messages.create(
            model=self._model,
            system=system_prompt,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            max_tokens=4096,
        )
        tool_use_block = next(b for b in response.content if b.type == "tool_use")
        return tool_use_block.input
