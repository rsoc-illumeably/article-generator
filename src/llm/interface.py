"""Abstract LLM interface.

Defines the contract that every concrete LLM client must satisfy.
Agents call only this interface — they are completely decoupled from
the underlying provider (Anthropic, OpenAI, etc.).

To swap providers: implement a new subclass and update the provider
value in config/app.yml. No agent code changes required.

Abstract methods:
    complete(system_prompt, messages, tools)
        — Sends a chat completion request and returns the model's response.
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
