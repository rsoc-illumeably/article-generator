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

# TODO: implement
