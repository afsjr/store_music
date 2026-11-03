from __future__ import annotations

import os
from pathlib import Path

# Mantém a suíte isolada de credenciais e do Supabase durante a coleta.
os.environ["LOCAL_MODE"] = "true"
os.environ["SUPABASE_DB_URL"] = ""

import pytest
from fastapi.testclient import TestClient

from app.adapters.memory.store import InMemoryStore
from app.adapters.rag.bm25 import BM25PolicyRetriever
from app.adapters.rag.pdf_loader import load_policy_chunks
from app.agent.tools import ToolRegistry
from app.config import Settings
from app.domain.services.catalog import CatalogService
from app.domain.services.conversations import ConversationService
from app.domain.services.orders import OrderService
from app.domain.services.policies import PolicyService
from app.domain.services.shipping import ShippingService
from app.main import create_app

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "emporio_musica" / "data"
POLICY_PDF = DATA_DIR / "políticas_da_loja.pdf"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        _env_file=None,
        data_dir=str(DATA_DIR),
        policy_pdf=str(POLICY_PDF),
        local_mode=True,
        store_today="2026-02-20",
        llm_provider="fake",
    )


@pytest.fixture
def store(settings: Settings) -> InMemoryStore:
    return InMemoryStore(settings.data_path, settings.store_today_date)


@pytest.fixture(scope="session")
def retriever() -> BM25PolicyRetriever:
    return BM25PolicyRetriever(load_policy_chunks(POLICY_PDF))


@pytest.fixture
def catalog(store: InMemoryStore) -> CatalogService:
    return CatalogService(store, store)


@pytest.fixture
def orders(store: InMemoryStore, settings: Settings) -> OrderService:
    return OrderService(store, store, settings.store_today_date)


@pytest.fixture
def policies(retriever: BM25PolicyRetriever, store: InMemoryStore) -> PolicyService:
    return PolicyService(retriever, store)


@pytest.fixture
def shipping() -> ShippingService:
    return ShippingService()


@pytest.fixture
def conversations(store: InMemoryStore, settings: Settings) -> ConversationService:
    return ConversationService(store, settings.max_history)


@pytest.fixture
def tools(catalog, orders, policies, shipping, conversations) -> ToolRegistry:
    return ToolRegistry(catalog, orders, policies, shipping, conversations)


@pytest.fixture
def client_factory(settings, store, retriever):
    def _factory(llm):
        app = create_app(settings=settings, store=store, retriever=retriever, llm=llm)
        return TestClient(app)

    return _factory
