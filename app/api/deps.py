from __future__ import annotations

from fastapi import Request

from app.agent.orchestrator import AgentOrchestrator
from app.domain.services.conversations import ConversationService


def get_agent(request: Request) -> AgentOrchestrator:
    return request.app.state.agent


def get_conversations(request: Request) -> ConversationService:
    return request.app.state.conversations
