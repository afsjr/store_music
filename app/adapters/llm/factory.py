from __future__ import annotations

import logging

from app.adapters.llm.base import UnavailableLLMClient
from app.adapters.llm.openai_compatible import FallbackLLMClient, OpenAICompatibleClient
from app.config import Settings

logger = logging.getLogger(__name__)


def build_llm_client(settings: Settings):
    provider = (settings.llm_provider or "deepseek").lower()
    if provider == "fake":
        return UnavailableLLMClient("LLM_PROVIDER=fake exige um cliente injetado.")

    if provider == "openai":
        if not settings.openai_api_key:
            return UnavailableLLMClient("OPENAI_API_KEY não configurada.")
        return OpenAICompatibleClient(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.llm_model or "gpt-4o-mini",
            timeout=settings.llm_timeout_seconds,
        )

    if provider == "deepseek":
        if not settings.deepseek_api_key:
            if settings.openai_api_key:
                logger.warning("DEEPSEEK_API_KEY ausente; usando OpenAI como provedor.")
                return OpenAICompatibleClient(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    model="gpt-4o-mini",
                    timeout=settings.llm_timeout_seconds,
                )
            return UnavailableLLMClient("DEEPSEEK_API_KEY não configurada.")
        primary = OpenAICompatibleClient(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.llm_model or "deepseek-flash",
            timeout=settings.llm_timeout_seconds,
        )
        fallback = None
        if settings.openai_api_key:
            fallback = OpenAICompatibleClient(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model="gpt-4o-mini",
                timeout=settings.llm_timeout_seconds,
            )
        return FallbackLLMClient(primary, fallback)

    return UnavailableLLMClient(f"Provedor de LLM desconhecido: {settings.llm_provider}")
