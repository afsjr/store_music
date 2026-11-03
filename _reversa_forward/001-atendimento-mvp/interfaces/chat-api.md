# Interface: Chat API

> Identificador: `001-atendimento-mvp`
> Contrato: `POST /api/chat`
> Tipo: HTTP JSON

## Requisição

```json
{
  "session_id": "uuid-da-sessao",
  "message": "Quais violões custam até R$ 1000?"
}
```

| Campo | Tipo | Obrigatório | Regra |
|-------|------|-------------|-------|
| session_id | string | Sim | UUID existente ou novo identificador aceito pela API. |
| message | string | Sim | Entre 1 e 2.000 caracteres. |

## Resposta de sucesso

Status: `200 OK`

```json
{
  "session_id": "uuid-da-sessao",
  "reply": "Encontrei estas opções...",
  "citations": [
    {
      "section": "6.2",
      "page": 6,
      "source": "Manual de Políticas"
    }
  ],
  "handoff": false,
  "tool_calls": [
    {
      "name": "buscar_produtos",
      "arguments": {"preco_max": 1000, "categoria": "Violões"}
    }
  ]
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| session_id | string | Sessão usada na conversa. |
| reply | string | Resposta final do agente. |
| citations | array | Seções e páginas usadas em respostas de política. |
| handoff | boolean | Indica se a conversa foi escalonada. |
| tool_calls | array | Ferramentas chamadas na rodada. |

## Erros

| Status | Código | Quando | Corpo |
|--------|--------|--------|-------|
| 422 | `validation_error` | Mensagem vazia ou acima de 2.000 caracteres. | `{"detail": "Mensagem deve ter entre 1 e 2000 caracteres."}` |
| 429 | `rate_limited` | Limite de requisições por sessão. | `{"detail": "Aguarde 60 segundos antes de tentar novamente."}` |
| 503 | `agent_unavailable` | LLM e fallback indisponíveis. | `{"detail": "Atendimento temporariamente indisponível. Tente novamente."}` |
| 500 | `internal_error` | Erro inesperado. | `{"detail": "Erro interno. Tente novamente."}` |

## Timeout e idempotência

- 🟡 Timeout do cliente: 30 segundos.
- 🟡 Timeout do agente: 25 segundos, com fallback de provedor.
- 🟡 A operação não é idempotente por natureza; o mesmo `session_id` e a mesma mensagem podem gerar respostas diferentes por causa do histórico.
- 🟡 A UI deve desabilitar o envio enquanto aguarda a resposta.
- 🟡 O backend deve registrar `request_id` e latência.

## Segurança

- 🟡 Não retornar telefone ou e-mail completos.
- 🟡 Não expor stack trace.
- 🟡 Limitar o tamanho da entrada e sanitizar o conteúdo antes de registrar.
