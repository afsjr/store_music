from __future__ import annotations

import json
import logging
from collections.abc import Sequence

from openai import OpenAI

from app.adapters.llm.base import LLMError
from app.domain.models import LLMResponse, ToolCall

logger = logging.getLogger(__name__)


class OpenAICompatibleClient:
    """Cliente para APIs compatíveis com OpenAI, incluindo DeepSeek."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_tokens: int = 800,
        extra_body: dict | None = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.extra_body = extra_body
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=1,
        )

    def complete(self, messages: Sequence[dict], tools: Sequence[dict]) -> LLMResponse:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=list(messages),
                tools=list(tools) if tools else None,
                tool_choice="auto" if tools else None,
                temperature=0.0,
                max_tokens=self.max_tokens,
                extra_body=self.extra_body,
            )
        except Exception as exc:  # noqa: BLE001 - o fallback precisa capturar qualquer falha
            logger.warning("Falha na chamada do LLM %s: %s", self.model, exc)
            raise LLMError(str(exc)) from exc

        choice = response.choices[0].message
        tool_calls: list[ToolCall] = []
        for tool_call in choice.tool_calls or []:
            raw_arguments = tool_call.function.arguments or "{}"
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                arguments = {"_raw": raw_arguments}
            tool_calls.append(
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=arguments,
                )
            )
        return LLMResponse(
            content=choice.content,
            tool_calls=tool_calls,
            raw=response.model_dump(),
        )


class FallbackLLMClient:
    """Tenta o provedor principal e recorre ao secundário em caso de erro."""

    def __init__(self, primary, fallback=None) -> None:
        self.primary = primary
        self.fallback = fallback

    def complete(self, messages: Sequence[dict], tools: Sequence[dict]) -> LLMResponse:
        try:
            return self.primary.complete(messages, tools)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Provedor principal falhou: %s", exc)
            if self.fallback is None:
                raise
            logger.info("Acionando provedor de fallback.")
            return self.fallback.complete(messages, tools)
