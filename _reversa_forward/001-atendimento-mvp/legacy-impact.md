# Legacy Impact: Agente de Atendimento Empório da Música — MVP

> Identificador: `001-atendimento-mvp`
> Data: `2026-11-03`
> Política de edição: `allowLegacyEdits: true`, `allowedPaths: []` (liberação irrestrita informada nesta sessão).

**Feature greenfield, sem legado pré-existente. Âncora: `prd.md` + specs SDD.**

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `app/config.py` | Plataforma de dados e API | componente-novo | LOW | Configuração central e caminhos de dados/políticas. |
| `app/logging.py` | Conversa e atendimento | componente-novo | LOW | Logs com request_id e mascaramento de PII. |
| `app/domain/models.py` | Todos | componente-novo | LOW | Entidades compartilhadas do domínio. |
| `app/domain/ports.py` | Todos | componente-novo | LOW | Contratos de repositório, LLM e retriever. |
| `app/domain/services/catalog.py` | Catálogo e promoções | componente-novo | LOW | Busca, promoção e PIX. |
| `app/domain/services/orders.py` | Pedidos e clientes | componente-novo | LOW | Identificação, pedidos e prazos. |
| `app/domain/services/policies.py` | Políticas e frete | componente-novo | LOW | RAG e informações da loja. |
| `app/domain/services/shipping.py` | Políticas e frete | componente-novo | LOW | Regra de frete local e cotação. |
| `app/domain/services/conversations.py` | Conversa e atendimento | componente-novo | LOW | Histórico, mensagens e handoffs. |
| `app/adapters/memory/store.py` | Plataforma de dados | componente-novo | LOW | Fallback em memória a partir dos CSVs. |
| `app/adapters/supabase/store.py` | Plataforma de dados | componente-novo | LOW | Repositórios SQL no Supabase. |
| `app/adapters/rag/pdf_loader.py` | Políticas e frete | componente-novo | LOW | Extração e cache do manual. |
| `app/adapters/rag/bm25.py` | Políticas e frete | componente-novo | LOW | Recuperação lexical por seção. |
| `app/adapters/llm/base.py` | Conversa e atendimento | componente-novo | LOW | Protocolo e fake de LLM. |
| `app/adapters/llm/openai_compatible.py` | Conversa e atendimento | componente-novo | LOW | Cliente DeepSeek/OpenAI e fallback. |
| `app/adapters/llm/factory.py` | Conversa e atendimento | componente-novo | LOW | Seleção de provedor. |
| `app/agent/prompts.py` | Conversa e atendimento | componente-novo | LOW | Persona e regras de negócio. |
| `app/agent/tools.py` | Todos | componente-novo | LOW | Ferramentas determinísticas. |
| `app/agent/guardrails.py` | Conversa e atendimento | componente-novo | LOW | Escopo, PII e bloqueio sem tool. |
| `app/agent/orchestrator.py` | Conversa e atendimento | componente-novo | LOW | Loop de tool calling e handoff. |
| `app/api/schemas.py` | API e UI | componente-novo | LOW | Contratos de entrada e saída. |
| `app/api/routes.py` | API e UI | componente-novo | LOW | Endpoints de chat, sessão e health. |
| `app/api/deps.py` | API e UI | componente-novo | LOW | Injeção de dependências. |
| `app/main.py` | API e UI | componente-novo | LOW | Composição da aplicação e middleware. |
| `app/web/index.html`, `styles.css`, `app.js` | API e UI | componente-novo | LOW | Interface de chat. |
| `supabase/migrations/001_schema.sql` | Plataforma de dados | componente-novo | LOW | Schema, view, índices e RLS. |
| `scripts/ingest.py` | Plataforma de dados | componente-novo | LOW | Ingestão e relatório de qualidade. |
| `scripts/build_policy_index.py` | Políticas e frete | componente-novo | LOW | Build e cache do índice. |
| `scripts/run_examples.py` | Documentação | componente-novo | LOW | Runner de exemplos. |
| `tests/` | Qualidade | componente-novo | LOW | 47 testes automatizados. |
| `examples/` | Documentação | componente-novo | LOW | 5 conversas de referência. |
| `README.md`, `docs/` | Documentação | componente-novo | LOW | Instruções, decisões e relatórios. |
| `data/policy_chunks.json` | Políticas e frete | componente-novo | LOW | Cache do manual para startup rápido. |

## Diff conceitual por componente

- **Conversa e atendimento:** novo loop de tool calling com limite de iterações, persona da loja, memória de 12 mensagens, guardrails e fallback de provedor.
- **Catálogo e promoções:** nova camada de consulta que aplica filtros, promoção ativa, PIX e status de estoque.
- **Pedidos e clientes:** nova identificação leve e consulta restrita ao próprio pedido, com mascaramento de PII.
- **Políticas e frete:** novo pipeline de extração, chunking, BM25 e citação de seção/página.
- **Plataforma de dados:** novo schema Supabase, ingestão idempotente e fallback em memória.
- **API e UI:** novos endpoints FastAPI e interface web de chat.

## Preservadas

Não aplicável: feature greenfield, sem regras de legado extraídas.

## Modificadas

Não aplicável: feature greenfield, sem regras de legado extraídas.
