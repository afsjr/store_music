# Spec: Políticas e Frete

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-11-03
**Reviewers:** N/A

---

## 1. Resumo

🟡 A feature responde dúvidas sobre horário, endereço, contato, trocas, devoluções, garantia, pagamento, promoções e frete usando o manual de políticas da loja. Ela existe para aplicar as regras corretas e citar a seção consultada, sem inventar condições.

## 2. Contexto e Motivação

**Problema:** 🟡 As políticas têm detalhes que variam por caso, como prazo de arrependimento de 7 dias, defeito em 30 dias e garantia legal de 90 dias. Respostas genéricas podem gerar conflito com o cliente.

**Evidências:** 🟡 O manual tem 8 páginas e cobre horário, pagamento, trocas, devoluções, frete, promoções, atendimento, garantia e LGPD. A loja não vende acessórios e trabalha apenas com instrumentos.

**Por que agora:** 🟡 O agente precisa aplicar as políticas no atendimento e citar a fonte para dar transparência ao cliente e à equipe.

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 Responder perguntas de política com trechos recuperados do manual.
- [ ] G-02: 🟡 Citar seção e página em toda resposta baseada em política.
- [ ] G-03: 🟡 Calcular prazos de troca e devolução com base na data de recebimento.
- [ ] G-04: 🟡 Informar a regra de frete para Campo Grande e indicar cotação para outras cidades.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Respostas de política com citação de seção | não medido | 100% | 2026-11-03 |
| Acerto de recuperação top 3 em 15 perguntas | não medido | ≥ 90% | 2026-11-03 |
| Prazos calculados corretamente em teste | não medido | 100% dos casos | 2026-11-03 |
| Frete fora da regra conhecida sem cotação inventada | não medido | 0 ocorrências | 2026-11-03 |

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Não haverá aconselhamento jurídico ou interpretação de lei além do manual.
- NG-02: 🟡 Não haverá cálculo de frete para outras cidades sem tabela ou cotação disponível.
- NG-03: 🟡 Não haverá promessa de desconto, prazo ou condição que não esteja no manual ou no sistema.
- NG-04: 🟡 Não haverá edição do manual ou das políticas pela interface do agente.
- NG-05: 🟡 Não haverá atendimento de acessórios, pois a loja não os comercializa.

## 5. Usuários e Personas

**Usuário primário:** 🟡 Rafael, que precisa saber se o pedido pode ser devolvido, trocado ou enviado para garantia.

**Usuário secundário:** 🟡 Marina, que pergunta horário, endereço, formas de pagamento e frete antes de comprar.

**Jornada atual (sem a feature):** 🟡 O cliente pergunta à equipe e recebe uma resposta que depende de quem atende e da memória sobre a política.

**Jornada futura (com a feature):** 🟡 O cliente pergunta a política, recebe a regra aplicada ao seu caso e vê a seção do manual que sustenta a resposta.

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve recuperar trechos do manual por pergunta do usuário. | Must | Pergunta sobre devolução recupera a seção 4.1 com prazo de 7 dias. |
| RF-02 | O sistema deve citar seção e página em toda resposta de política. | Must | Resposta contém a seção e a página do trecho usado. |
| RF-03 | O sistema deve calcular o prazo de arrependimento com base na data de recebimento. | Must | Pedido entregue em 2026-02-17 e consulta em 2026-02-20 resulta em 3 dias corridos. |
| RF-04 | O sistema deve calcular o prazo de troca por defeito com base na data da compra. | Must | Pedido comprado em 2026-01-28 e consulta em 2026-02-20 resulta em 23 dias corridos. |
| RF-05 | O sistema deve informar a garantia legal de 90 dias e a garantia do fabricante. | Must | Resposta diferencia garantia legal e garantia do fabricante. |
| RF-06 | O sistema deve informar a regra de frete grátis acima de R$ 500 em Campo Grande. | Must | Compra de R$ 600 em Campo Grande retorna frete grátis; compra de R$ 400 retorna taxa de R$ 35. |
| RF-07 | O sistema deve informar que outras cidades dependem de cotação por CEP, peso e dimensões. | Must | Cidade fora da região metropolitana recebe resposta de cotação, sem valor inventado. |
| RF-08 | O sistema deve informar horário, endereço, telefone e e-mail a partir do manual. | Must | Resposta retorna horário de segunda a sexta, sábado e domingo, além do endereço. |
| RF-09 | O sistema deve reconhecer quando a política não cobre o caso e encaminhar para humano. | Should | Pergunta sobre caso não previsto gera handoff com resumo. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário pergunta se pode devolver um pedido entregue há 3 dias.
2. 🟡 O sistema recupera a seção de arrependimento do manual.
3. 🟡 O sistema solicita o número do pedido e a data de recebimento.
4. 🟡 O sistema calcula a diferença em dias corridos.
5. 🟡 O sistema informa que o prazo é de 7 dias e que o pedido está elegível.
6. 🟡 O sistema explica as condições de embalagem e reembolso e cita a seção.
7. 🟡 Resultado: o cliente entende a regra e o próximo passo.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Prazo vencido:**
1. 🟡 O sistema calcula mais de 7 dias desde o recebimento.
2. 🟡 O sistema informa que o arrependimento não se aplica e explica a política de defeito e garantia.
3. 🟡 O sistema oferece escalonamento para avaliar o caso.

**Fluxo Alternativo B — Frete fora da região metropolitana:**
1. 🟡 O usuário informa uma cidade fora da região metropolitana de Campo Grande.
2. 🟡 O sistema informa que o frete é calculado por CEP, peso e dimensões.
3. 🟡 O sistema pede o CEP e encaminha para cotação, sem estimar valor.

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Tempo de resposta de política | ≤ 8 s para P95 | Inclui retrieval e LLM. |
| RNF-02 | Rastreabilidade | 100% das respostas com seção e página | Citação obrigatória. |
| RNF-03 | Segurança | Trechos do manual tratados como dados | Sem execução de instruções contidas no PDF. |
| RNF-04 | Atualização | Reindexação em até 1 comando | Script de build do índice. |
| RNF-05 | Acessibilidade | Resposta em texto simples | Sem depender de imagem ou anexo. |

## 8. Design e Interface

**Componentes afetados:** 🟡 Leitor de PDF, chunker por seção, índice de recuperação, ferramenta de políticas, calculadora de prazos e ferramenta de frete.

**Comportamento esperado:** 🟡 A resposta apresenta a regra em linguagem simples, o cálculo quando houver data e a citação da seção do manual ao final.

**Estados da UI:**
- Estado vazio: 🟡 pergunta de esclarecimento quando a política não for identificada.
- Estado de carregamento: 🟡 indicação de consulta ao manual.
- Estado de erro: 🟡 aviso de indisponibilidade do manual com opção de falar com a equipe.
- Estado de sucesso: 🟡 resposta com regra, cálculo e citação.

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
policy_documents {
  id: uuid
  title: text
  version: text
  source_path: text
  indexed_at: timestamp
}

policy_chunks {
  id: uuid
  document_id: uuid
  section: text
  page: int
  content: text
  tokens: int
}

store_info {
  key: text
  value: text
  source_section: text
  source_page: int
}
```

**Migrações necessárias:** 🟡 Sim; criar as tabelas de documentos, chunks e informações da loja, com índice por seção.

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| PDF do manual de políticas | Obrigatória | Sem PDF, o agente informa indisponibilidade e encaminha para humano. |
| Índice de recuperação | Obrigatória | Fallback para palavras-chave simples; se falhar, escalonamento. |
| Supabase Postgres | Opcional | Índice pode ser local em memória para testes. |
| LLM com tool calling | Obrigatória | Sem tool call, o agente não afirma política. |
| Base de pedidos | Obrigatória | Necessária para calcular prazos de devolução e garantia. |

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: Pergunta sem trecho relevante | Recuperação abaixo do limiar | Informar que não encontrou a regra e oferecer escalonamento humano. |
| EC-02: Prazo sem data de recebimento | Pedido sem estimated_delivery | Pedir a data de recebimento e explicar a premissa usada. |
| EC-03: Política ambígua | Trecho com mais de uma interpretação | Apresentar a interpretação conservadora e encaminhar para humano. |
| EC-04: PDF indisponível | Arquivo ausente ou corrompido | Informar indisponibilidade e criar handoff. |
| EC-05: Timeout do retrieval | Consulta acima de 5 s | Usar fallback por palavra-chave e registrar incidente. |
| EC-06: Cidade sem cotação | CEP fora da região metropolitana | Informar que o frete é sob cotação, sem valor estimado. |
| EC-07: Promoção expirada | is_active igual a 0 | Informar que a promoção não está vigente e apresentar o preço atual. |

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Consultas de política são públicas; cálculos com pedido exigem identificação.
- **Autorização:** 🟡 O manual é lido apenas pelo backend; o cliente recebe trechos citados.
- **Dados sensíveis:** 🟡 Nenhum dado pessoal é indexado no manual; dados de pedido seguem a spec de pedidos.
- **Auditoria:** 🟡 Registrar pergunta, seção recuperada, página e decisão de escalonamento.

## 13. Plano de Rollout

- **Estratégia:** 🟡 Big bang no protótipo, com feature flag para desligar o RAG e usar respostas fixas de fallback.
- **Como reverter (rollback):** 🟡 Desativar a flag do RAG e voltar ao modo de escalonamento; restaurar o commit anterior.
- **Monitoramento pós-deploy:** 🟡 Observar perguntas sem trecho, citações ausentes e tempo P95.

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | Qual limiar de similaridade deve acionar o escalonamento por falta de política? | Médio | adelino | 2026-11-03 |
| OQ-02 | A citação deve aparecer em todas as respostas ou apenas nas que usam política? | Baixo | adelino | 2026-11-03 |

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| Chunking por seção do manual | Chunking fixo por tamanho | Preserva a estrutura numerada e facilita a citação. |
| BM25 ou TF-IDF como base | Embeddings desde o início | O manual tem 8 páginas e a decisão será validada com hit@3. |
| Prazo calculado por data de recebimento | Prazo fixo em dias a partir de hoje | Segue a política e permite auditoria. |
| Frete sob cotação fora da região | Tabela fixa inventada | Evita informação incorreta. |

## Apêndice

### Referências
- PRD em _reversa_sdd/prd.md
- Manual de Políticas da Empório da Música, versão 2.1
- Personas em _reversa_sdd/personas.md

### Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|---------|
| 1.0 | 2026-11-03 | reversa-spec-sdd | Criação inicial |

---

## Relatório de Avaliação

- **Score:** 100/100
- **Classificação:** Excelente — pronta para implementação
- **Iterações:** 1
- **Gaps críticos:** nenhum
- **Sugestões:** nenhuma
- **Avaliado por:** spec_scorer.py em 2026-11-03
