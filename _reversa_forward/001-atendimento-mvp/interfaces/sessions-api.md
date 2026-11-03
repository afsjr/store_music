# Interface: Sessões e Histórico

> Identificador: `001-atendimento-mvp`
> Contratos: `POST /api/sessions` e `GET /api/sessions/{session_id}/messages`
> Tipo: HTTP JSON

## Criar sessão

### Requisição

```json
{}
```

### Resposta de sucesso

Status: `201 Created`

```json
{
  "session_id": "uuid-da-sessao",
  "created_at": "2026-11-03T15:00:00Z"
}
```

### Erros

| Status | Código | Quando |
|--------|--------|--------|
| 500 | `internal_error` | Falha ao criar a sessão. |
| 503 | `storage_unavailable` | Banco e fallback indisponíveis. |

## Consultar histórico

### Requisição

```http
GET /api/sessions/{session_id}/messages?limit=50
```

| Parâmetro | Tipo | Obrigatório | Regra |
|-----------|------|-------------|-------|
| session_id | string | Sim | UUID da sessão. |
| limit | integer | Não | Padrão 50, máximo 200. |

### Resposta de sucesso

Status: `200 OK`

```json
{
  "session_id": "uuid-da-sessao",
  "messages": [
    {
      "role": "user",
      "content": "Quais violões custam até R$ 1000?",
      "created_at": "2026-11-03T15:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Encontrei estas opções...",
      "citations": [],
      "created_at": "2026-11-03T15:00:02Z"
    }
  ]
}
```

### Erros

| Status | Código | Quando |
|--------|--------|--------|
| 404 | `session_not_found` | Sessão inexistente. |
| 422 | `validation_error` | Limite inválido. |
| 503 | `storage_unavailable` | Banco e fallback indisponíveis. |

## Regras

- 🟡 O histórico é ordenado por `created_at` crescente.
- 🟡 Mensagens de ferramenta não são exibidas na UI, apenas registradas para auditoria.
- 🟡 O session_id é um UUID aleatório e não contém dados pessoais.
- 🟡 Não há autenticação na v1; a proteção é o identificador não adivinhável.
