# Actions: Agente de Atendimento Empório da Música — MVP

> Identificador: `001-atendimento-mvp`
> Data: `2026-11-03`
> Roadmap: `_reversa_forward/001-atendimento-mvp/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 30 |
| Paralelizáveis (`[//]`) | 17 |
| Maior cadeia de dependência | 8 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar metadados do projeto, dependências e variáveis de ambiente de exemplo. | - | `[//]` | `pyproject.toml`, `requirements.txt`, `.env.example` | 🟡 | `[ ]` |
| T002 | Criar módulo de configuração com Pydantic Settings e logging estruturado. | T001 | `[//]` | `app/config.py`, `app/logging.py` | 🟡 | `[ ]` |
| T003 | Criar entidades de domínio e protocolos de repositório, LLM e retriever. | T002 | - | `app/domain/models.py`, `app/domain/ports.py` | 🟡 | `[ ]` |
| T004 | Criar store em memória que carrega os CSVs e monta índices de busca. | T003 | `[//]` | `app/adapters/memory/store.py` | 🟡 | `[ ]` |
| T005 | Criar migration SQL do Supabase com tabelas, view, extensões e índices. | T003 | `[//]` | `supabase/migrations/001_schema.sql` | 🟡 | `[ ]` |
| T006 | Criar store Supabase com consultas parametrizadas e persistência de conversas. | T005 | - | `app/adapters/supabase/store.py` | 🟡 | `[ ]` |
| T007 | Criar leitor de PDF, chunker por seção e retriever TF-IDF com citações. | T003 | `[//]` | `app/adapters/rag/pdf_loader.py`, `app/adapters/rag/tfidf.py` | 🟡 | `[ ]` |
| T008 | Criar protocolo de LLM, fake scriptado e adapter OpenAI-compatible com factory. | T003 | `[//]` | `app/adapters/llm/base.py`, `fake.py`, `openai_compatible.py`, `factory.py` | 🟡 | `[ ]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Escrever testes de catálogo, promoções e regra de PIX. | T004 | `[//]` | `tests/test_catalog.py` | 🟡 | `[ ]` |
| T010 | Escrever testes de identificação, pedidos e privacidade. | T004 | `[//]` | `tests/test_orders.py` | 🟡 | `[ ]` |
| T011 | Escrever testes de recuperação de políticas e citações. | T007 | `[//]` | `tests/test_policies.py` | 🟡 | `[ ]` |
| T012 | Escrever testes de ferramentas e guardrails. | T008 | `[//]` | `tests/test_tools.py` | 🟡 | `[ ]` |
| T013 | Escrever testes do loop do agente com LLM fake. | T008 | `[//]` | `tests/test_agent.py` | 🟡 | `[ ]` |
| T014 | Escrever testes dos endpoints da API com TestClient. | T002 | `[//]` | `tests/test_api.py` | 🟡 | `[ ]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Implementar serviço de catálogo e promoções sobre os repositórios. | T004 | - | `app/domain/services/catalog.py` | 🟡 | `[ ]` |
| T016 | Implementar serviço de clientes, identificação e pedidos. | T004 | - | `app/domain/services/orders.py` | 🟡 | `[ ]` |
| T017 | Implementar serviço de políticas, informações da loja e frete. | T007 | - | `app/domain/services/policies.py`, `shipping.py` | 🟡 | `[ ]` |
| T018 | Implementar registro de ferramentas com schemas Pydantic e handlers. | T015, T016, T017 | - | `app/agent/tools.py` | 🟡 | `[ ]` |
| T019 | Implementar guardrails de escopo, PII e bloqueio de resposta sem tool call. | T018 | - | `app/agent/guardrails.py` | 🟡 | `[ ]` |
| T020 | Implementar orquestrador com loop de tool calling, limite e fallback. | T018, T019 | - | `app/agent/orchestrator.py` | 🟡 | `[ ]` |
| T021 | Implementar persistência de conversas, mensagens e handoffs. | T006 | - | `app/domain/services/conversations.py` | 🟡 | `[ ]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T022 | Criar schemas Pydantic, dependências e rotas FastAPI. | T020, T021 | - | `app/api/schemas.py`, `app/api/routes.py`, `app/main.py` | 🟡 | `[ ]` |
| T023 | Criar UI de chat com HTML, CSS e JavaScript vanilla. | T022 | `[//]` | `app/web/index.html`, `app.js`, `styles.css` | 🟡 | `[ ]` |
| T024 | Criar script de ingestão com validação, upsert e relatório de qualidade. | T005, T006 | - | `scripts/ingest.py` | 🟡 | `[ ]` |
| T025 | Criar script de build do índice de políticas. | T007 | `[//]` | `scripts/build_policy_index.py` | 🟡 | `[ ]` |
| T026 | Criar runner de exemplos e gerar 3 a 5 conversas em markdown. | T022 | - | `scripts/run_examples.py`, `examples/` | 🟡 | `[ ]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T027 | Adicionar logs de request_id, latência, tool calls e erros amigáveis. | T022 | `[//]` | `app/logging.py`, `app/api/routes.py` | 🟡 | `[ ]` |
| T028 | Escrever README com setup, arquitetura, decisões, limitações e uso de IA. | T026 | `[//]` | `README.md` | 🟡 | `[ ]` |
| T029 | Criar `.env.example`, Makefile e documentação de execução local. | T001 | `[//]` | `.env.example`, `Makefile`, `docs/` | 🟡 | `[ ]` |
| T030 | Executar testes, lint e validação final; atualizar status das ações. | T009-T029 | - | `tests/`, `README.md` | 🟡 | `[ ]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-03 | Versão inicial gerada por `/reversa-to-do` | reversa |
