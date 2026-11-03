# Interface: Health Check

> Identificador: `001-atendimento-mvp`
> Contrato: `GET /health`
> Tipo: HTTP JSON

## Requisição

```http
GET /health
```

## Resposta de sucesso

Status: `200 OK`

```json
{
  "status": "ok",
  "database": "ok",
  "llm": "ok",
  "mode": "local",
  "version": "1.0.0"
}
```

| Campo | Tipo | Valores | Descrição |
|-------|------|---------|-----------|
| status | string | ok, degraded, error | Estado geral. |
| database | string | ok, memory, unavailable | Fonte de dados ativa. |
| llm | string | ok, fallback, unavailable | Provedor de LLM. |
| mode | string | local, supabase | Modo de execução. |
| version | string | semver | Versão da aplicação. |

## Resposta degradada

Status: `200 OK` com `status: degraded` quando o banco está em memória ou o LLM está em fallback.

## Resposta de erro

Status: `503 Service Unavailable`

```json
{
  "status": "error",
  "database": "unavailable",
  "llm": "unavailable",
  "mode": "local",
  "version": "1.0.0"
}
```

## Regras

- 🟡 O health check deve responder em no máximo 1 segundo.
- 🟡 Não deve expor chaves, URLs internas ou stack trace.
- 🟡 Deve ser seguro para monitoramento frequente.
- 🟡 Em modo local, `database` pode ser `memory` e `status` pode ser `ok`.
