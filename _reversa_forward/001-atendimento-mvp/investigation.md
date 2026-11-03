# Investigation: Agente de Atendimento Empório da Música — MVP

> Identificador: `001-atendimento-mvp`
> Data: `2026-11-03`
> Requirements: `_reversa_forward/001-atendimento-mvp/requirements.md`

## 1. Perguntas de investigação

🟡 A investigação buscou responder:

1. Qual abordagem de agente reduz alucinação em preço, estoque e pedido?
2. Qual LLM oferece melhor custo-benefício e confiabilidade de tool calling em português?
3. Qual estratégia de recuperação é suficiente para um manual de 8 páginas?
4. Como manter o projeto testável sem depender de Supabase ou de rede?
5. Qual interface entrega uma demonstração clara dentro do prazo?

## 2. Abordagens avaliadas

| Abordagem | Vantagens | Riscos | Decisão |
|-----------|-----------|--------|---------|
| Agente SQL livre | Flexibilidade para perguntas abertas | Alucinação, injeção, difícil auditoria | Descartada |
| ReAct sem ferramentas | Loop simples | Pode inventar dados e não consulta o sistema | Descartada |
| Function calling com ferramentas determinísticas | Precisão, auditoria e baixo acoplamento | Exige definir contratos de ferramenta | Adotada |
| RAG com embeddings | Melhor recall semântico | Custo e dependência extra para 8 páginas | Adiada |
| RAG TF-IDF/BM25 por seção | Sem custo extra, determinístico e testável | Recall lexical menor | Adotada |
| Manual inteiro no prompt | Implementação simples | Custo por chamada e não demonstra retrieval | Descartada |

## 3. Comparativo de LLMs

🟡 Valores de tabela consultados em 03/11/2026 nos sites oficiais.

| Modelo | Entrada por 1M | Saída por 1M | Contexto | Free tier | Tool calling | Observação |
|--------|---------------|-------------|----------|-----------|--------------|------------|
| DeepSeek Flash | US$ 0,15 off-peak / 0,30 peak | US$ 0,60 off-peak / 1,20 peak | 1M | Não | Sim | Melhor custo; provedor chinês exige atenção à LGPD. |
| OpenAI gpt-4o-mini | US$ 0,15 | US$ 0,60 | 128k | Não | Sim, maduro | Maior previsibilidade de schema. |
| Gemini 3.8 Flash | Grátis no free tier / US$ 0,75 pago | Grátis / US$ 3,75 | 1M | Sim | Sim | Free tier usa dados para treino e tem rate limit. |

**Conclusão:** DeepSeek Flash como padrão, OpenAI `gpt-4o-mini` como fallback. Gemini fica documentado como alternativa gratuita, sem bloquear o MVP.

## 4. Estratégia de recuperação

🟡 O manual tem 8 páginas e seções numeradas. A estratégia escolhida:

1. Extrair texto com preservação de páginas.
2. Limpar cabeçalhos, rodapés e numeração.
3. Dividir por seções numeradas e subseções.
4. Normalizar acentos e caixa.
5. Indexar com TF-IDF e recuperar top-3 por similaridade de cosseno.
6. Anexar seção e página aos trechos para citação.

Critério de sucesso: acerto top-3 em pelo menos 90% de 15 perguntas de política. Se ficar abaixo, avaliar híbrido com embeddings.

## 5. Padrões aplicáveis

- **Hexagonal architecture / ports and adapters:** domínio isolado de banco, LLM e PDF.
- **Repository:** contratos para catálogo, pedidos, clientes, conversas e handoffs.
- **Tool calling:** ferramentas com schemas Pydantic e execução determinística.
- **Guardrail pós-geração:** bloquear resposta que afirma dado sem tool call.
- **Fallback:** repositório em memória e provedor alternativo de LLM.
- **Idempotência:** upsert na ingestão e chave de sessão na conversa.

## 6. Fontes consultadas

- Documentação de preços do DeepSeek: https://api-docs.deepseek.com/quick_start/pricing
- Documentação de preços da OpenAI: https://platform.openai.com/docs/pricing
- Documentação de preços e rate limits do Gemini: https://ai.google.dev/gemini-api/docs/pricing
- Manual de Políticas da Empório da Música, versão 2.1
- PRD e specs SDD em `_reversa_sdd/`
- CSVs de produtos, clientes, pedidos, itens e promoções

## 7. Riscos de pesquisa

🟡 Preços e modelos mudam com frequência; o README deve registrar a data da consulta. O free tier do Gemini não é adequado para dados reais por causa do uso para treino. O DeepSeek exige avaliação de conformidade em produção.

## 8. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-03 | Versão inicial gerada por `/reversa-plan` | reversa |
