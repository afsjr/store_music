from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.llm.base import UnavailableLLMClient
from app.adapters.llm.factory import build_llm_client
from app.adapters.memory.store import InMemoryStore
from app.adapters.rag.bm25 import BM25PolicyRetriever
from app.adapters.rag.pdf_loader import load_policy_chunks
from app.agent.orchestrator import AgentOrchestrator
from app.agent.tools import ToolRegistry
from app.api.routes import router as api_router
from app.config import Settings, get_settings
from app.domain.services.catalog import CatalogService
from app.domain.services.conversations import ConversationService
from app.domain.services.orders import OrderService
from app.domain.services.policies import PolicyService
from app.domain.services.shipping import ShippingService
from app.logging import configure_logging, get_logger, new_request_id, request_id_var

logger = get_logger(__name__)
WEB_DIR = Path(__file__).parent / "web"


def build_store(settings: Settings):
    if settings.supabase_enabled:
        db_url = settings.supabase_db_url or ""
        if db_url.startswith(("http://", "https://")):
            logger.error(
                "SUPABASE_DB_URL parece ser a URL da API. Use a connection string "
                "Postgres (postgresql://...) do painel do Supabase. Usando modo local."
            )
            return InMemoryStore(settings.data_path, settings.store_today_date), "local"
        try:
            from app.adapters.supabase.store import SupabaseStore

            return SupabaseStore(db_url), "supabase"
        except Exception:  # noqa: BLE001
            logger.exception(
                "Não foi possível conectar ao Supabase; usando o modo local em memória."
            )
    return InMemoryStore(settings.data_path, settings.store_today_date), "local"


def build_retriever(settings: Settings):
    try:
        chunks = load_policy_chunks(
            settings.policy_pdf_path,
            cache_path=settings.policy_cache_path,
        )
        return BM25PolicyRetriever(chunks)
    except Exception:  # noqa: BLE001
        logger.exception("Não foi possível indexar o manual de políticas.")
        return BM25PolicyRetriever([])


def create_app(
    *,
    settings: Settings | None = None,
    store=None,
    llm=None,
    retriever=None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    if store is None:
        store, store_mode = build_store(settings)
    else:
        store_mode = "supabase" if store.__class__.__name__ == "SupabaseStore" else "local"

    retriever = retriever or build_retriever(settings)
    llm = llm or build_llm_client(settings)

    catalog = CatalogService(store, store)
    orders = OrderService(store, store, settings.store_today_date)
    policies = PolicyService(retriever, store)
    shipping = ShippingService()
    conversations = ConversationService(store, settings.max_history)
    tools = ToolRegistry(catalog, orders, policies, shipping, conversations)
    agent = AgentOrchestrator(
        llm=llm,
        tools=tools,
        conversations=conversations,
        settings=settings,
    )

    app = FastAPI(
        title="Empório da Música — Agente de Atendimento",
        version="1.0.0",
        description="Agente de atendimento por mensagens de texto para a Empório da Música.",
    )
    app.state.settings = settings
    app.state.store = store
    app.state.retriever = retriever
    app.state.llm = llm
    app.state.conversations = conversations
    app.state.agent = agent
    app.state.store_mode = store_mode
    app.state.llm_available = not isinstance(llm, UnavailableLLMClient)
    app.state.policy_available = getattr(retriever, "count", lambda: 0)() > 0

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = new_request_id()
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s -> %s em %.1f ms",
                request.method,
                request.url.path,
                getattr(locals().get("response"), "status_code", "erro"),
                elapsed_ms,
            )
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(api_router)
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    return app


app = create_app()
