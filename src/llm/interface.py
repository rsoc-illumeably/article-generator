"""Abstract LLM interface.

Defines the contract that every concrete LLM client must satisfy.
Agents call only this interface — they are completely decoupled from
the underlying provider (Anthropic, OpenAI, etc.).

To swap providers: implement a new subclass and update the provider
value in config/app.yml. No agent code changes required.

Abstract methods:
    complete(system_prompt, messages, tools)
        — Sends a chat completion request and returns the model's response.
    complete_structured(system_prompt, messages, tool)
        — Forces a single tool call and returns its input arguments as a dict.
          The provider API guarantees the dict conforms to the tool's schema,
          so no text parsing or format enforcement is needed by the caller.
"""

import abc
from typing import Optional


class LLMInterface(abc.ABC):

    @abc.abstractmethod
    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> str:
        """Send a chat completion request and return the model's text response.

        Args:
            system_prompt: The system-level instruction for the model.
            messages: Conversation turns in provider-neutral format,
                e.g. [{"role": "user", "content": "..."}].
            tools: Optional list of tool definitions to make available.
                None means no tools; an explicit list enables those tools.

        Returns:
            The model's response as a plain text string.
        """

    @abc.abstractmethod
    def complete_structured(
        self,
        system_prompt: str,
        messages: list[dict],
        tool: dict,
    ) -> dict:
        """Force a single tool call and return its input arguments as a dict.

        The provider is instructed to call the given tool unconditionally.
        The returned dict is the tool's input arguments, guaranteed by the
        provider API to conform to the tool's input_schema — no text parsing
        required by the caller.

        Args:
            system_prompt: The system-level instruction for the model.
            messages: Conversation turns in provider-neutral format.
            tool: A single tool definition including its input_schema.

        Returns:
            The tool call input arguments as a plain Python dict.
        """
