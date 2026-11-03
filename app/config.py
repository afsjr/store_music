from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação carregada de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "local"
    log_level: str = "INFO"

    data_dir: str = "emporio_musica/data"
    policy_pdf: str = "emporio_musica/data/políticas_da_loja.pdf"
    policy_cache: str = "data/policy_chunks.json"
    local_mode: bool = True
    store_today: str | None = None

    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-flash"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"

    supabase_db_url: str | None = None

    max_history: int = Field(default=12, ge=1, le=100)
    max_tool_iterations: int = Field(default=5, ge=1, le=20)
    llm_timeout_seconds: float = Field(default=30.0, gt=0)
    llm_max_tokens: int = Field(default=800, ge=100, le=4000)
    llm_thinking: bool = False

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def policy_pdf_path(self) -> Path:
        return Path(self.policy_pdf)

    @property
    def policy_cache_path(self) -> Path:
        return Path(self.policy_cache)

    @property
    def store_today_date(self) -> date:
        if self.store_today:
            return date.fromisoformat(self.store_today)
        return date.today()

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_db_url) and not self.local_mode

    @property
    def llm_configured(self) -> bool:
        if self.llm_provider == "fake":
            return True
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return bool(self.deepseek_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
