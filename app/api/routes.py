from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.adapters.llm.base import LLMUnavailableError
from app.api.deps import get_agent, get_conversations
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    CitationOut,
    HealthResponse,
    HistoryResponse,
    MessageOut,
    SessionResponse,
    ToolCallOut,
)
from app.domain.services.conversations import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    conversations: ConversationService = Depends(get_conversations),
) -> SessionResponse:
    session = conversations.create_session()
    return SessionResponse(session_id=session.session_id, created_at=session.created_at)


@router.post("/api/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    agent=Depends(get_agent),
) -> ChatResponse:
    try:
        result = agent.chat(payload.session_id, payload.message)
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Atendimento temporariamente indisponível. Configure o provedor de LLM.",
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="O atendimento demorou mais que o esperado. Tente novamente.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao processar chat")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a mensagem. Tente novamente.",
        ) from exc

    return ChatResponse(
        session_id=result.session_id,
        reply=result.reply,
        citations=[CitationOut(**citation.model_dump()) for citation in result.citations],
        handoff=result.handoff,
        tool_calls=[
            ToolCallOut(name=tool.name, arguments=tool.arguments, ok=tool.ok)
            for tool in result.tool_calls
        ],
    )


@router.get("/api/sessions/{session_id}/messages", response_model=HistoryResponse)
def history(
    session_id: str,
    limit: int = 50,
    conversations: ConversationService = Depends(get_conversations),
) -> HistoryResponse:
    if not conversations.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    messages = conversations.history(session_id, limit=max(1, min(limit, 200)))
    return HistoryResponse(
        session_id=session_id,
        messages=[
            MessageOut(
                role=message.role,
                content=message.content,
                citations=[CitationOut(**c.model_dump()) for c in message.citations],
                created_at=message.created_at,
            )
            for message in messages
            if message.role in ("user", "assistant")
        ],
    )


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    store_mode = getattr(request.app.state, "store_mode", "local")
    llm_available = bool(getattr(request.app.state, "llm_available", False))
    policy_available = bool(getattr(request.app.state, "policy_available", False))
    database = "memory" if store_mode == "local" else "ok"

    if not llm_available:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "database": database,
                "llm": "unavailable",
                "mode": store_mode,
                "version": "1.0.0",
                "policy": "ok" if policy_available else "unavailable",
            },
        )

    return HealthResponse(
        status="ok" if policy_available else "degraded",
        database=database,
        llm="ok",
        mode=store_mode,
        version="1.0.0",
        policy="ok" if policy_available else "unavailable",
    )
