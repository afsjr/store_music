from __future__ import annotations

import logging

from app.adapters.llm.base import UnavailableLLMClient
from app.adapters.llm.openai_compatible import FallbackLLMClient, OpenAICompatibleClient
from app.config import Settings

logger = logging.getLogger(__name__)


def _openai_client(settings: Settings) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        api_key=settings.openai_api_key or "",
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        timeout=settings.llm_timeout_seconds,
        max_tokens=settings.llm_max_tokens,
    )


def _deepseek_client(settings: Settings) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        api_key=settings.deepseek_api_key or "",
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.llm_timeout_seconds,
        max_tokens=settings.llm_max_tokens,
        extra_body={"thinking": {"type": "enabled" if settings.llm_thinking else "disabled"}},
    )


def build_llm_client(settings: Settings):
    provider = (settings.llm_provider or "deepseek").lower()
    if provider == "fake":
        return UnavailableLLMClient("LLM_PROVIDER=fake exige um cliente injetado.")

    if provider == "openai":
        if not settings.openai_api_key:
            if settings.deepseek_api_key:
                logger.warning("OPENAI_API_KEY ausente; usando DeepSeek como provedor.")
                return _deepseek_client(settings)
            return UnavailableLLMClient("OPENAI_API_KEY não configurada.")
        primary = _openai_client(settings)
        fallback = _deepseek_client(settings) if settings.deepseek_api_key else None
        return FallbackLLMClient(primary, fallback)

    if provider == "deepseek":
        if not settings.deepseek_api_key:
            if settings.openai_api_key:
                logger.warning("DEEPSEEK_API_KEY ausente; usando OpenAI como provedor.")
                return _openai_client(settings)
            return UnavailableLLMClient("DEEPSEEK_API_KEY não configurada.")
        primary = _deepseek_client(settings)
        fallback = _openai_client(settings) if settings.openai_api_key else None
        return FallbackLLMClient(primary, fallback)

    return UnavailableLLMClient(f"Provedor de LLM desconhecido: {settings.llm_provider}")
