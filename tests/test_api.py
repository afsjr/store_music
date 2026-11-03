from __future__ import annotations

from app.adapters.llm.base import FakeLLMClient, UnavailableLLMClient
from app.domain.models import LLMResponse, ToolCall


def test_health(client_factory):
    client = client_factory(FakeLLMClient([]))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["llm"] == "ok"
    assert response.headers["X-Request-ID"]


def test_create_session(client_factory):
    client = client_factory(FakeLLMClient([]))
    response = client.post("/api/sessions")
    assert response.status_code == 201
    assert response.json()["session_id"]


def test_chat(client_factory):
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
            LLMResponse(content="Encontrei o Yamaha C40 por R$ 599,90."),
        ]
    )
    client = client_factory(llm)
    session_id = client.post("/api/sessions").json()["session_id"]
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Quais violões até R$ 1000?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "R$" in data["reply"]
    assert data["tool_calls"]


def test_empty_message_is_rejected(client_factory):
    client = client_factory(FakeLLMClient([]))
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 422


def test_history(client_factory):
    llm = FakeLLMClient([LLMResponse(content="Olá! Como posso ajudar?")])
    client = client_factory(llm)
    session_id = client.post("/api/sessions").json()["session_id"]
    client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá"},
    )
    response = client.get(f"/api/sessions/{session_id}/messages")
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert messages[0]["role"] == "user"
    assert messages[-1]["role"] == "assistant"


def test_unknown_session_returns_404(client_factory):
    client = client_factory(FakeLLMClient([]))
    response = client.get("/api/sessions/nao-existe/messages")
    assert response.status_code == 404


def test_unavailable_llm_returns_503(client_factory):
    client = client_factory(UnavailableLLMClient("sem chave"))
    assert client.get("/health").status_code == 503
    response = client.post("/api/chat", json={"message": "Olá"})
    assert response.status_code == 503
