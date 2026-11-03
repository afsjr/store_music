from __future__ import annotations

from app.adapters.llm.base import FakeLLMClient
from app.agent.guardrails import out_of_scope_response, safe_fallback_response
from app.agent.orchestrator import AgentOrchestrator
from app.domain.models import LLMResponse, ToolCall


def _agent(settings, tools, conversations, llm):
    return AgentOrchestrator(
        llm=llm,
        tools=tools,
        conversations=conversations,
        settings=settings,
    )


def test_agent_uses_tool_and_answers(settings, tools, conversations):
    llm = FakeLLMClient(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="1",
                        name="buscar_produtos",
                        arguments={"categoria": "Violões", "preco_max": 1000},
                    )
                ]
            ),
            LLMResponse(
                content=(
                    "Encontrei o Yamaha C40 por R$ 599,90 e o Tagima Memphis AC-39 por R$ 429,90."
                )
            ),
        ]
    )
    agent = _agent(settings, tools, conversations, llm)
    reply = agent.chat(None, "Quais violões custam até R$ 1000?")
    assert reply.tool_calls
    assert reply.tool_calls[0].name == "buscar_produtos"
    assert "R$" in reply.reply
    assert reply.handoff is False


def test_agent_blocks_price_without_tool(settings, tools, conversations):
    llm = FakeLLMClient([LLMResponse(content="O preço é R$ 100,00.")])
    agent = _agent(settings, tools, conversations, llm)
    reply = agent.chat(None, "Quanto custa?")
    assert reply.reply == safe_fallback_response()
    assert reply.handoff is True


def test_agent_handles_out_of_scope_without_llm(settings, tools, conversations):
    llm = FakeLLMClient([])
    agent = _agent(settings, tools, conversations, llm)
    reply = agent.chat(None, "Vocês vendem cordas de violão?")
    assert reply.reply == out_of_scope_response()
    assert llm.calls == []


def test_agent_respects_max_tool_iterations(settings, tools, conversations):
    def always_tool(messages, tool_schemas):
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    id="loop",
                    name="buscar_produtos",
                    arguments={"termo": "violão"},
                )
            ]
        )

    llm = FakeLLMClient(always_tool)
    agent = _agent(settings, tools, conversations, llm)
    reply = agent.chat(None, "Quero um violão")
    assert reply.handoff is True
    assert reply.reply == safe_fallback_response()


def test_agent_returns_policy_citations(settings, tools, conversations):
    llm = FakeLLMClient(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="1",
                        name="consultar_politicas",
                        arguments={"pergunta": "posso devolver um pedido?"},
                    )
                ]
            ),
            LLMResponse(
                content=(
                    "O arrependimento é permitido em até 7 dias corridos após o recebimento, "
                    "com o produto na embalagem original."
                )
            ),
        ]
    )
    agent = _agent(settings, tools, conversations, llm)
    reply = agent.chat(None, "Posso devolver?")
    assert reply.citations
    assert reply.citations[0].section == "4.1"


def test_agent_order_flow(settings, tools, conversations):
    llm = FakeLLMClient(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="1",
                        name="identificar_cliente",
                        arguments={
                            "nome": "Ana Carolina Ferreira",
                            "contato": "(67) 99654-7821",
                        },
                    )
                ]
            ),
            LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="2",
                        name="consultar_pedido",
                        arguments={"order_id": 8, "customer_id": 2},
                    )
                ]
            ),
            LLMResponse(
                content=(
                    "Seu pedido 8 está enviado, com rastreio BRJL5544332BR e previsão "
                    "de entrega para 28/02/2026."
                )
            ),
        ]
    )
    agent = _agent(settings, tools, conversations, llm)
    reply = agent.chat(None, "Meu pedido 8 chegou?")
    assert len(reply.tool_calls) == 2
    assert "BRJL5544332BR" in reply.reply
    assert reply.handoff is False
