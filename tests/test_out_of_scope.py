from __future__ import annotations

import pytest

from app.adapters.llm.base import FakeLLMClient
from app.agent.guardrails import (
    general_out_of_scope_response,
    is_out_of_scope_topic,
    out_of_scope_response,
)
from app.agent.orchestrator import AgentOrchestrator

OUT_OF_SCOPE_MESSAGES = [
    "Qual a capital da França?",
    "Vocês são melhores que a concorrente?",
    "Preciso de um advogado para processar a loja",
    "Meu filho está com febre, qual remédio devo dar?",
    "Quem vai ganhar a eleição?",
    "Qual o jogo do Flamengo hoje?",
    "Qual a previsão do tempo para amanhã?",
    "Quanto custa uma geladeira?",
]


@pytest.mark.parametrize("message", OUT_OF_SCOPE_MESSAGES)
def test_detects_out_of_scope_topics(message):
    assert is_out_of_scope_topic(message) is True


IN_SCOPE_MESSAGES = [
    "Qual a política de devolução?",
    "Quero trocar por preferência",
    "Quanto custa o Takamine GD20?",
    "Vocês vendem violão?",
    "Qual o prazo de entrega?",
]


@pytest.mark.parametrize("message", IN_SCOPE_MESSAGES)
def test_does_not_block_store_topics(message):
    assert is_out_of_scope_topic(message) is False


def test_accessory_response_does_not_promise_partner_list():
    response = out_of_scope_response()
    assert "loja parceira" not in response
    assert "encaminhar" in response


def test_agent_blocks_general_out_of_scope_without_llm(settings, tools, conversations):
    llm = FakeLLMClient([])
    agent = AgentOrchestrator(
        llm=llm,
        tools=tools,
        conversations=conversations,
        settings=settings,
    )
    reply = agent.chat(None, "Qual a capital da França?")
    assert reply.reply == general_out_of_scope_response()
    assert llm.calls == []


def test_agent_keeps_accessory_response(settings, tools, conversations):
    llm = FakeLLMClient([])
    agent = AgentOrchestrator(
        llm=llm,
        tools=tools,
        conversations=conversations,
        settings=settings,
    )
    reply = agent.chat(None, "Vocês vendem cordas de violão?")
    assert reply.reply == out_of_scope_response()
    assert llm.calls == []
