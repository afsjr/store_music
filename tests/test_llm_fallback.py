from __future__ import annotations

import pytest

from app.adapters.llm.base import FakeLLMClient, LLMError
from app.adapters.llm.factory import build_llm_client
from app.adapters.llm.openai_compatible import FallbackLLMClient
from app.config import Settings
from app.domain.models import LLMResponse


class FailingLLM:
    def complete(self, messages, tools):
        raise LLMError("provedor principal indisponível")


def _settings(provider: str) -> Settings:
    return Settings(
        _env_file=None,
        llm_provider=provider,
        deepseek_api_key="deepseek-key",
        openai_api_key="openai-key",
        deepseek_model="deepseek-flash",
        openai_model="gpt-4o-mini",
        local_mode=True,
    )


@pytest.mark.parametrize(
    ("provider", "primary_model", "fallback_model"),
    [
        ("deepseek", "deepseek-flash", "gpt-4o-mini"),
        ("openai", "gpt-4o-mini", "deepseek-flash"),
    ],
)
def test_factory_sets_other_provider_as_fallback(provider, primary_model, fallback_model):
    client = build_llm_client(_settings(provider))
    assert isinstance(client, FallbackLLMClient)
    assert client.primary.model == primary_model
    assert client.fallback is not None
    assert client.fallback.model == fallback_model


def test_fallback_client_uses_secondary_provider():
    fallback = FakeLLMClient([LLMResponse(content="resposta do fallback")])
    client = FallbackLLMClient(FailingLLM(), fallback)
    response = client.complete([{"role": "user", "content": "oi"}], [])
    assert response.content == "resposta do fallback"
