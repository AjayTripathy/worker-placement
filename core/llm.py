from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, prompt: str, system: str = "") -> str: ...


class AnthropicClient:
    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 1024):
        import anthropic
        self._client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str, system: str = "") -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system or "You are a precise legal and data analysis assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text


class NullLLMClient:
    """Raises clearly if LLM fallback is invoked without a client configured."""
    def complete(self, prompt: str, system: str = "") -> str:
        raise RuntimeError(
            "LLM fallback invoked but no LLMClient configured. "
            "Pass an AnthropicClient to TieredRuleInterpreter or provide a compiled implementation."
        )
