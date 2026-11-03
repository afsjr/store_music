from __future__ import annotations

from collections.abc import Callable, Sequence

from app.domain.models import LLMResponse


class LLMError(RuntimeError):
    """Erro genérico de LLM."""


class LLMUnavailableError(LLMError):
    """Nenhum provedor de LLM está configurado ou disponível."""


class UnavailableLLMClient:
    def __init__(self, message: str = "Nenhum provedor de LLM configurado.") -> None:
        self.message = message

    def complete(self, messages: Sequence[dict], tools: Sequence[dict]) -> LLMResponse:
        raise LLMUnavailableError(self.message)


class FakeLLMClient:
    """LLM scriptado para testes e exemplos determinísticos."""

    def __init__(
        self,
        responses: Sequence[LLMResponse] | Callable[[Sequence[dict], Sequence[dict]], LLMResponse],
    ) -> None:
        self._responses = list(responses) if not callable(responses) else None
        self._callable = responses if callable(responses) else None
        self.calls: list[list[dict]] = []

    def complete(self, messages: Sequence[dict], tools: Sequence[dict]) -> LLMResponse:
        self.calls.append([dict(message) for message in messages])
        if self._callable is not None:
            return self._callable(messages, tools)
        if not self._responses:
            raise LLMError("FakeLLMClient sem respostas restantes.")
        return self._responses.pop(0)
