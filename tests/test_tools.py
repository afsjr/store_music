from __future__ import annotations

from app.agent.guardrails import (
    is_accessory_request,
    safe_fallback_response,
    sanitize_response,
)
from app.domain.models import ToolResult


def test_buscar_produtos_tool(tools):
    result = tools.execute(
        "buscar_produtos",
        {"categoria": "Violões", "preco_max": 1000, "limite": 5},
        "sessao",
    )
    assert result.ok is True
    assert 0 < len(result.result["produtos"]) <= 5
    assert all(item["preco_efetivo"] <= 1000 for item in result.result["produtos"])


def test_identificar_cliente_tool(tools):
    result = tools.execute(
        "identificar_cliente",
        {"nome": "Ana Carolina Ferreira", "contato": "(67) 99654-7821"},
        "sessao",
    )
    assert result.ok is True
    assert result.result["status"] == "ok"
    assert result.result["cliente"]["customer_id"] == 2
    assert result.result["cliente"]["telefone"] == "****7821"


def test_consultar_pedido_tool(tools):
    result = tools.execute("consultar_pedido", {"order_id": 8, "customer_id": 2}, "sessao")
    assert result.ok is True
    assert result.result["status"] == "ok"
    assert result.result["pedido"]["rastreio"] == "BRJL5544332BR"


def test_consultar_pedido_denies_other_customer(tools):
    result = tools.execute("consultar_pedido", {"order_id": 8, "customer_id": 7}, "sessao")
    assert result.ok is True
    assert result.result["status"] == "nao_encontrado"


def test_calcular_frete_tool(tools):
    local = tools.execute("calcular_frete", {"cidade": "Campo Grande", "subtotal": 600}, "sessao")
    distant = tools.execute("calcular_frete", {"cidade": "Dourados", "subtotal": 600}, "sessao")
    assert local.result["kind"] == "gratis"
    assert distant.result["kind"] == "cotacao"


def test_escalar_atendimento_tool(tools, conversations):
    session = conversations.create_session()
    result = tools.execute(
        "escalar_atendimento",
        {"motivo": "reclamação", "resumo": "Cliente pediu suporte humano."},
        session.session_id,
    )
    assert result.ok is True
    assert result.result["protocolo"]


def test_accessory_detection():
    assert is_accessory_request("Vocês vendem cordas de violão?") is True
    assert is_accessory_request("Quero um amplificador para guitarra") is True
    assert is_accessory_request("Violão com cordas de nylon") is False
    assert is_accessory_request("Quais violões até R$ 1000?") is False


def test_guardrail_blocks_price_without_tool():
    reply, blocked = sanitize_response("O preço é R$ 999,00.", [], has_tool_history=False)
    assert blocked is True
    assert reply == safe_fallback_response()


def test_guardrail_allows_price_with_tool():
    tool_result = ToolResult(
        name="buscar_produtos",
        arguments={},
        result={"produtos": []},
        ok=True,
    )
    reply, blocked = sanitize_response(
        "O preço é R$ 999,00.", [tool_result], has_tool_history=False
    )
    assert blocked is False
    assert "R$" in reply


def test_guardrail_preserves_store_contacts():
    reply, blocked = sanitize_response(
        "Fale com a gente no (67) 3321-4500 ou contato@emporiodamusica.com.br",
        [],
        has_tool_history=True,
    )
    assert blocked is False
    assert "(67) 3321-4500" in reply
    assert "contato@emporiodamusica.com.br" in reply


def test_guardrail_masks_customer_phone():
    reply, blocked = sanitize_response(
        "Seu telefone é (67) 99654-7821",
        [],
        has_tool_history=True,
    )
    assert blocked is False
    assert "****7821" in reply
    assert "99654-7821" not in reply
