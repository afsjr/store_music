# Spec: Catálogo e Promoções

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-11-03
**Reviewers:** N/A

---

## 1. Resumo

🟡 A feature entrega consultas confiáveis ao catálogo de instrumentos, incluindo busca por termo, categoria e faixa de preço, detalhe de produto, estoque, status e promoções ativas. Ela existe para que o agente informe preço e disponibilidade somente com dados atuais da loja.

## 2. Contexto e Motivação

**Problema:** 🟡 Clientes perguntam preço, disponibilidade e promoções com frequência. Respostas desatualizadas geram frustração e risco de propaganda enganosa.

**Evidências:** 🟡 O catálogo tem 65 produtos, 62 ativos, 2 descontinuados, 1 com status coming_soon e 1 ativo com estoque zero. Existem 4 promoções ativas no arquivo de promoções.

**Por que agora:** 🟡 A v1 precisa cobrir o cenário principal do desafio: responder faixa de preço e disponibilidade com dados reais.

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 Responder buscas por termo, categoria e faixa de preço com até 10 resultados.
- [ ] G-02: 🟡 Informar preço, promoção ativa e estoque de cada produto consultado.
- [ ] G-03: 🟡 Aplicar a regra de PIX de 5% somente sobre preço não promocional.
- [ ] G-04: 🟡 Sinalizar produtos esgotados, descontinuados e coming_soon de forma explícita.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Consultas com preço vindo do banco | não medido | 100% | 2026-11-03 |
| Tempo de busca de catálogo | não medido | ≤ 2 s para P95 | 2026-11-03 |
| Produtos retornados por busca | não medido | ≤ 10 por resposta | 2026-11-03 |
| Promoções expiradas apresentadas como ativas | não medido | 0 ocorrências | 2026-11-03 |

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Não haverá carrinho, reserva de estoque ou checkout nesta versão.
- NG-02: 🟡 Não haverá negociação de preço nem desconto fora das promoções cadastradas.
- NG-03: 🟡 Não haverá comparação com preços de concorrentes ou marketplaces.
- NG-04: 🟡 Não haverá cadastro ou edição de produtos pela interface do agente.
- NG-05: 🟡 Não haverá recomendação de acessórios, pois a loja não os comercializa.

## 5. Usuários e Personas

**Usuário primário:** 🟡 Marina, cliente iniciante que pesquisa modelos e faixas de preço antes de comprar.

**Usuário secundário:** 🟡 Rafael, músico que confere especificações e disponibilidade de um modelo específico.

**Jornada atual (sem a feature):** 🟡 O cliente percorre o site ou pergunta à equipe, sem garantia de que o preço e o estoque estão atualizados.

**Jornada futura (com a feature):** 🟡 O cliente pergunta por faixa de preço ou modelo, recebe até 10 opções com preço e estoque e decide com segurança.

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve buscar produtos por termo no nome, descrição e especificações. | Must | Busca por Takamine retorna o produto GD20 com ID 95. |
| RF-02 | O sistema deve filtrar produtos por categoria e faixa de preço mínima e máxima. | Must | Busca por violões até R$ 1.000 retorna apenas produtos da categoria 5 com preço menor ou igual a 1.000. |
| RF-03 | O sistema deve retornar no máximo 10 produtos por consulta. | Must | Busca ampla retorna 10 itens e informa que há mais resultados. |
| RF-04 | O sistema deve informar preço de tabela, promoção ativa, preço promocional e estoque. | Must | Produto 127 retorna preço original, 10% de desconto e preço final calculado. |
| RF-05 | O sistema deve calcular o preço com PIX de 5% somente quando não houver promoção ativa. | Must | Produto 95 retorna R$ 2.089,05 no PIX; produto 127 não aplica PIX sobre o preço promocional. |
| RF-06 | O sistema deve sinalizar produto ativo com estoque zero como indisponível temporariamente. | Must | Produto 96 retorna status ativo, estoque 0 e aviso de indisponibilidade. |
| RF-07 | O sistema deve sinalizar produtos descontinuados e coming_soon sem oferecê-los como compra imediata. | Must | Produto 113 retorna descontinuado; produto 130 retorna coming_soon. |
| RF-08 | O sistema deve retornar especificações técnicas do produto quando solicitado. | Should | Detalhe do produto 81 retorna top, back_sides, neck, strings e scale. |
| RF-09 | O sistema deve informar quando a busca não encontrar produtos. | Must | Busca por produto inexistente retorna mensagem de nenhum resultado e sugestão de refinar. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário pergunta quais violões custam até R$ 1.000.
2. 🟡 O sistema identifica a categoria violões e o limite de preço.
3. 🟡 O sistema consulta o catálogo e aplica os filtros de status, preço e estoque.
4. 🟡 O sistema retorna até 10 produtos com nome, preço, promoção e disponibilidade.
5. 🟡 O sistema informa que produtos esgotados não estão disponíveis para compra imediata.
6. 🟡 Resultado: o usuário escolhe um modelo e pode pedir detalhe ou condição de pagamento.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Produto específico:**
1. 🟡 O usuário pergunta o preço do Takamine GD20.
2. 🟡 O sistema busca pelo nome e retorna o produto 95 com preço de tabela e condição de PIX.
3. 🟡 O sistema verifica que não há promoção ativa para o produto e informa o preço atual.

**Fluxo Alternativo B — Busca sem resultados:**
1. 🟡 O usuário busca por um modelo inexistente.
2. 🟡 O sistema informa que não encontrou resultados e pede para refinar marca, categoria ou faixa de preço.
3. 🟡 O sistema não inventa produto substituto.

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Tempo de consulta ao catálogo | ≤ 2 s para P95 | Consulta indexada no Supabase. |
| RNF-02 | Consistência de preço | 100% dos valores vindos do banco | Nenhum preço fixo no prompt. |
| RNF-03 | Segurança | Consultas parametrizadas | Sem concatenação de SQL com entrada do usuário. |
| RNF-04 | Disponibilidade | ≥ 99% em teste local | Fallback para CSV em memória. |
| RNF-05 | Acessibilidade | Preço com separador brasileiro | Formato R$ 1.234,56. |

## 8. Design e Interface

**Componentes afetados:** 🟡 Ferramenta de catálogo, view de ofertas, repositório de produtos, repositório de promoções e formatação de preço.

**Comportamento esperado:** 🟡 A resposta lista produtos em tópicos com nome, preço, promoção, estoque e um lembrete de que o valor final depende da forma de pagamento.

**Estados da UI:**
- Estado vazio: 🟡 mensagem de nenhum produto encontrado com sugestão de refinar a busca.
- Estado de carregamento: 🟡 indicação de consulta em andamento.
- Estado de erro: 🟡 mensagem de indisponibilidade do catálogo com opção de tentar novamente.
- Estado de sucesso: 🟡 lista de até 10 produtos com preço e estoque.

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
products {
  product_id: int
  name: text
  price_brl: numeric
  category_id: int
  description: text
  stock_quantity: int
  status: text          // active, discontinued, coming_soon
  specs: jsonb
  search_vector: tsvector
}

promotions {
  promotion_id: int
  product_id: int
  discount_percent: numeric
  description: text
  is_active: boolean
}

product_offers {
  product_id: int
  price_brl: numeric
  discount_percent: numeric
  effective_price: numeric
  has_active_promotion: boolean
}
```

**Migrações necessárias:** 🟡 Sim; criar a view product_offers e índices em categoria, preço, status e estoque.

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| Supabase Postgres | Obrigatória | Fallback para repositório em memória carregado dos CSVs. |
| CSVs de produtos, categorias e promoções | Obrigatória | Sem dados, a ferramenta retorna erro explícito e o agente oferece escalonamento. |
| LLM com tool calling | Obrigatória | Sem tool call, o agente não responde preço e pede nova tentativa. |

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: Busca sem resultados | Termo inexistente | Informar ausência de resultados e sugerir refinar categoria ou faixa de preço. |
| EC-02: Faixa de preço inválida | Preço mínimo maior que o máximo | Rejeitar a consulta e pedir para corrigir os valores. |
| EC-03: Produto com estoque zero | stock_quantity igual a 0 e status active | Informar indisponibilidade temporária e sugerir alternativa semelhante. |
| EC-04: Produto descontinuado | status discontinued | Informar que saiu do catálogo e sugerir modelo equivalente ativo. |
| EC-05: Produto coming_soon | status coming_soon | Informar que ainda não está à venda e não prometer data. |
| EC-06: Múltiplas promoções para o mesmo produto | Duas ou mais promoções ativas | Aplicar a de maior desconto e registrar a decisão no log. |
| EC-07: Timeout do banco | Consulta acima de 5 s | Acionar fallback em memória e registrar incidente. |

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Não há autenticação para consultar catálogo público.
- **Autorização:** 🟡 Apenas leitura de produtos, categorias e promoções.
- **Dados sensíveis:** 🟡 Nenhum dado pessoal é necessário para consulta de catálogo.
- **Auditoria:** 🟡 Registrar termo buscado, filtros aplicados e quantidade de resultados, sem dados pessoais.

## 13. Plano de Rollout

- **Estratégia:** 🟡 Big bang no protótipo, com feature flag para alternar entre Supabase e memória.
- **Como reverter (rollback):** 🟡 Desativar a flag do Supabase e usar o repositório em memória; restaurar o commit anterior.
- **Monitoramento pós-deploy:** 🟡 Observar consultas sem resultado, tempo P95 e divergência de preço entre banco e resposta.

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | Como tratar produtos com múltiplas promoções ativas quando os descontos forem iguais? | Baixo | adelino | 2026-11-03 |
| OQ-02 | A vitrine deve priorizar produtos em estoque na ordenação padrão? | Médio | adelino | 2026-11-03 |

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| Consultar catálogo por ferramenta determinística | LLM gerar SQL livre | Evita erro e injeção; mantém preço auditável. |
| Confiar nos campos estruturados do CSV | Corrigir descrições divergentes | Preserva a fonte operacional e documenta a inconsistência. |
| Aplicar PIX apenas sobre preço não promocional | Somar PIX à promoção | Segue a regra de não cumulatividade do manual. |
| Limitar a 10 resultados | Retornar catálogo completo | Mantém a resposta legível e controla custo de tokens. |

## Apêndice

### Referências
- PRD em _reversa_sdd/prd.md
- Manual de Políticas da Empório da Música, seções 6 e 7
- CSVs de produtos, categorias e promoções

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
