# Roadmap: Agente de Atendimento Empório da Música — MVP

> Identificador: `001-atendimento-mvp`
> Data: `2026-11-03`
> Requirements: `_reversa_forward/001-atendimento-mvp/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

🟡 A feature será construída como um monólito modular em Python, com arquitetura hexagonal: domínio e serviços independentes de fornecedores, portas para catálogo, pedidos, políticas, conversas e LLM, e adapters para Supabase, memória local, DeepSeek/OpenAI e leitura do PDF. O agente usa function calling com ferramentas determinísticas para dados estruturados e RAG lexical por seção para o manual de políticas. A API FastAPI serve uma UI vanilla de chat e expõe health check, sessões e histórico. O fallback em memória permite rodar testes e demonstração sem credenciais.

## 2. Princípios aplicados

🟡 Não existe `.reversa/principles.md` registrado no projeto. Os princípios adotados são os do PRD: alta coesão, baixo acoplamento, precisão antes de fluência, privacidade por padrão e simplicidade operacional.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Alta coesão e baixo acoplamento | Domínio depende de portas; adapters são substituíveis. | respeita |
| Precisão antes de fluência | Preço, estoque e pedido vêm de ferramentas determinísticas. | respeita |
| Privacidade por padrão | Identificação obrigatória e mascaramento de PII. | respeita |
| Simplicidade operacional | Fallback local e uma única aplicação FastAPI. | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Monólito modular em Python com FastAPI | Atende à restrição do desafio e concentra API, UI e agente em um processo. | Microsserviços, CLI isolada | 🟡 |
| D-02 | Arquitetura hexagonal com portas e adapters | Mantém o domínio testável e permite trocar Supabase, LLM e RAG. | Serviços acoplados ao ORM | 🟡 |
| D-03 | Function calling com ferramentas determinísticas | Evita SQL livre e reduz alucinação de preço, estoque e pedido. | Agente SQL, ReAct sem ferramentas | 🟡 |
| D-04 | RAG TF-IDF/BM25 por seção | Manual de 8 páginas; retrieval lexical é suficiente e de baixo custo. | Embeddings, manual inteiro no prompt | 🟡 |
| D-05 | DeepSeek Flash como LLM padrão | Melhor custo-benefício e suporte a tool calls. | OpenAI, Gemini | 🟡 |
| D-06 | OpenAI `gpt-4o-mini` como fallback | Tool calling previsível e mesmo patamar de preço. | Apenas DeepSeek | 🟡 |
| D-07 | Supabase Postgres como fonte principal | Requisito do usuário e permite SQL completo. | SQLite, apenas memória | 🟡 |
| D-08 | Repositório em memória carregado dos CSVs | Permite testes e demonstração sem credenciais. | Docker com Supabase local | 🟡 |
| D-09 | Persistência de conversas, mensagens e handoffs | Histórico e auditoria do atendimento. | Sem persistência | 🟡 |
| D-10 | Memória de 12 mensagens por sessão | Equilíbrio entre contexto e custo de tokens. | Histórico completo no prompt | 🟡 |
| D-11 | Guardrail que bloqueia resposta sem tool call | Impede afirmação de preço, estoque ou prazo sem consulta. | Confiar apenas no prompt | 🟡 |
| D-12 | Identificação leve por nome + telefone ou e-mail | Dados disponíveis e menor atrito. | Login com senha, CPF | 🟡 |
| D-13 | `STORE_TODAY` configurável | Permite reproduzir cenários de prazo nos exemplos. | Data fixa no código | 🟡 |
| D-14 | UI vanilla HTML/CSS/JS | Sem framework frontend e com baixo acoplamento. | React, Streamlit | 🟡 |
| D-15 | Testes com fakes de LLM e repositórios | Execução rápida e sem dependência de rede. | Testes apenas E2E | 🟡 |

## 4. Premissas

🟡 Não há marcadores `[DÚVIDA]` no requirements. As premissas abaixo são de projeto e ficam registradas para validação futura.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| Orçamento baixo, uso de DeepSeek/OpenAI e Gemini free apenas em desenvolvimento | Seção 10, Lacunas | Custo maior que o esperado. |
| Credenciais do Supabase e DeepSeek serão fornecidas em `.env` antes da demonstração | Seção 2, Contexto | Modo local apenas, sem dados persistidos. |
| O prazo de 03/11/2026 até 19h é horário local | Seção 2, Contexto | Atraso na entrega. |
| A UI e a API serão executadas localmente, sem deploy | Seção 1, Resumo executivo | Avaliação limitada ao ambiente local. |

## 5. Delta arquitetural

🟡 O projeto é greenfield; todos os componentes são novos. A tabela registra a arquitetura alvo e a origem da decisão nas specs.

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `app/domain` | `_reversa_sdd/sdd/conversa-atendimento.md#6-requisitos-funcionais` | componente-novo | Entidades, portas e serviços de catálogo, pedidos, políticas e conversa. |
| `app/adapters/supabase` | `_reversa_sdd/sdd/plataforma-dados.md#6-requisitos-funcionais` | componente-novo | Repositórios SQL e persistência de conversas. |
| `app/adapters/memory` | `_reversa_sdd/sdd/plataforma-dados.md#6-requisitos-funcionais` | componente-novo | Repositórios em memória carregados dos CSVs. |
| `app/adapters/llm` | `_reversa_sdd/sdd/conversa-atendimento.md#6-requisitos-funcionais` | componente-novo | Cliente DeepSeek/OpenAI e loop de tool calling. |
| `app/adapters/rag` | `_reversa_sdd/sdd/politicas-frete.md#6-requisitos-funcionais` | componente-novo | Leitura do PDF, chunking e índice TF-IDF. |
| `app/agent` | `_reversa_sdd/sdd/conversa-atendimento.md#6-requisitos-funcionais` | componente-novo | Orquestrador, ferramentas, prompts e guardrails. |
| `app/api` e `app/web` | `_reversa_sdd/sdd/api-ui.md#6-requisitos-funcionais` | contrato-novo | Endpoints FastAPI e UI de chat. |
| `scripts/` | `_reversa_sdd/sdd/plataforma-dados.md#6-requisitos-funcionais` | componente-novo | Ingestão, build do índice e benchmark. |

## 6. Delta no modelo de dados

🟡 O modelo é novo e deriva dos CSVs mais as tabelas de conversa, mensagens, handoffs, chunks de política e controle de ingestão.

- Resumo das mudanças: nove tabelas de domínio e atendimento, uma view de ofertas e índices para busca textual e consultas por cliente/pedido.
- Detalhe completo em: `_reversa_forward/001-atendimento-mvp/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Chat | HTTP | `_reversa_forward/001-atendimento-mvp/interfaces/chat-api.md` |
| Sessões e histórico | HTTP | `_reversa_forward/001-atendimento-mvp/interfaces/sessions-api.md` |
| Health check | HTTP | `_reversa_forward/001-atendimento-mvp/interfaces/health-api.md` |

## 8. Plano de migração

1. 🟡 Criar o schema e as migrations no Supabase.
2. 🟡 Executar a ingestão dos seis CSVs com validação e relatório de qualidade.
3. 🟡 Construir o índice de políticas a partir do PDF.
4. 🟡 Configurar `.env` com `SUPABASE_DB_URL`, `DEEPSEEK_API_KEY` e demais variáveis.
5. 🟡 Subir a aplicação e validar o health check.
6. 🟡 Executar os testes e gerar os exemplos de conversa.
7. 🟡 Revisar o README e as limitações conhecidas.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Prazo curto até 19h | alto | alta | MVP enxuto, fallback local e priorização das specs Must. |
| Dados inconsistentes nos CSVs | médio | alta | Validação na ingestão e suposições documentadas. |
| Alucinação de preço ou estoque | alto | média | Ferramentas determinísticas e guardrail de tool call. |
| Credenciais ausentes | médio | média | Modo local em memória e `.env.example`. |
| Vazamento de PII | alto | baixa | Identificação, mascaramento e testes de privacidade. |
| Rate limit ou indisponibilidade do LLM | médio | baixa | Retry com backoff e fallback de provedor. |
| PDF ou índice indisponível | médio | baixa | Fallback por palavra-chave e escalonamento. |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Testes automatizados passando sem credenciais externas
- [ ] Três a cinco exemplos de conversa gerados
- [ ] README com setup, decisões, limitações e uso de IA
- [ ] Health check e UI validados localmente

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-03 | Versão inicial gerada por `/reversa-plan` | reversa |
