# Spec: Pedidos e Clientes

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-11-03
**Reviewers:** N/A

---

## 1. Resumo

🟡 A feature permite identificar o cliente de forma leve e consultar somente os pedidos vinculados a ele, com status, itens, rastreio e previsão de entrega. Ela existe para responder dúvidas de pós-venda sem expor dados de outros clientes.

## 2. Contexto e Motivação

**Problema:** 🟡 Rafael e outros clientes precisam saber se o pedido foi confirmado, enviado ou entregue. A equipe consulta planilhas e sistemas para responder, o que consome tempo.

**Evidências:** 🟡 Existem 20 pedidos no CSV, com status delivered, shipped, confirmed, pending e cancelled. Apenas pedidos enviados e entregues têm código de rastreamento.

**Por que agora:** 🟡 O desafio pede que o agente saiba consultar status de pedido em tempo real e aplicar regras de privacidade.

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 Identificar o cliente por nome combinado com telefone ou e-mail.
- [ ] G-02: 🟡 Retornar somente pedidos vinculados ao cliente identificado.
- [ ] G-03: 🟡 Exibir status, itens, total, rastreio e previsão de entrega.
- [ ] G-04: 🟡 Bloquear qualquer consulta sem identificação suficiente.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Consultas de pedido com vínculo validado | não medido | 100% | 2026-11-03 |
| Vazamento de dados entre clientes em teste | não medido | 0 ocorrências | 2026-11-03 |
| Tempo de consulta de pedido | não medido | ≤ 2 s para P95 | 2026-11-03 |
| Pedidos com status exibido corretamente | não medido | 100% dos 20 pedidos | 2026-11-03 |

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Não haverá criação, alteração ou cancelamento de pedido nesta versão.
- NG-02: 🟡 Não haverá listagem de todos os clientes ou busca por nome sem vínculo.
- NG-03: 🟡 Não haverá autenticação com senha, token ou CPF, pois esses dados não existem na base.
- NG-04: 🟡 Não haverá cálculo de reembolso ou estorno; apenas consulta e encaminhamento.
- NG-05: 🟡 Não haverá consulta de pedidos de terceiros, mesmo com número do pedido.

## 5. Usuários e Personas

**Usuário primário:** 🟡 Rafael, músico pós-venda que precisa conferir status, rastreio ou previsão do próprio pedido.

**Usuário secundário:** 🟡 Equipe de atendimento que recebe o escalonamento quando a identificação falha.

**Jornada atual (sem a feature):** 🟡 O cliente liga ou envia mensagem, informa o número do pedido e espera a equipe consultar o sistema.

**Jornada futura (com a feature):** 🟡 O cliente informa o número do pedido e se identifica; o agente valida o vínculo e responde com os dados do pedido.

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve solicitar número do pedido e uma identificação do cliente antes de consultar. | Must | Consulta sem identificação retorna pedido de nome e telefone ou e-mail. |
| RF-02 | O sistema deve comparar nome normalizado e telefone ou e-mail para localizar o cliente. | Must | Cliente 7 é localizado por Thiago Barbosa Lima e telefone ou e-mail correspondente. |
| RF-03 | O sistema deve validar se o pedido pertence ao cliente identificado. | Must | Pedido 8 de outro cliente é negado sem revelar dados. |
| RF-04 | O sistema deve retornar status, total, data do pedido e previsão de entrega. | Must | Pedido 8 retorna status shipped e previsão 2026-02-28. |
| RF-05 | O sistema deve retornar itens do pedido com nome, quantidade e preço unitário. | Must | Pedido 15 retorna produtos 82 e 106 com quantidades. |
| RF-06 | O sistema deve retornar código de rastreamento quando existir. | Must | Pedido 8 retorna BRJL5544332BR; pedido 13 não retorna rastreio. |
| RF-07 | O sistema deve explicar o significado de cada status em linguagem de cliente. | Must | cancelled é explicado como cancelado, com motivo quando disponível. |
| RF-08 | O sistema deve mascarar telefone e e-mail na resposta de confirmação. | Must | Resposta mostra apenas os quatro últimos dígitos do telefone. |
| RF-09 | O sistema deve encaminhar para humano quando não conseguir identificar o cliente. | Should | Após duas tentativas, cria handoff com resumo da conversa. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário informa o número do pedido e o nome completo.
2. 🟡 O sistema solicita telefone ou e-mail para confirmar a identidade.
3. 🟡 O usuário informa o telefone.
4. 🟡 O sistema normaliza os dados e localiza o cliente.
5. 🟡 O sistema valida o vínculo entre o cliente e o pedido.
6. 🟡 O sistema responde com status, itens, total, rastreio e previsão.
7. 🟡 Resultado: o cliente recebe os dados do próprio pedido e o atendimento é registrado.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Pedido não encontrado:**
1. 🟡 O sistema não localiza o número do pedido.
2. 🟡 O sistema pede para conferir o número e informa que pode encaminhar para a equipe.
3. 🟡 O sistema não revela se o pedido pertence a outra pessoa.

**Fluxo Alternativo B — Identificação divergente:**
1. 🟡 O nome, telefone ou e-mail não correspondem ao cliente do pedido.
2. 🟡 O sistema nega a consulta e pede para confirmar os dados.
3. 🟡 Após duas falhas, o sistema oferece escalonamento humano.

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Tempo de consulta de pedido | ≤ 2 s para P95 | Consulta indexada por cliente e pedido. |
| RNF-02 | Privacidade | 0 dados de outro cliente em resposta | Teste automatizado com dois clientes distintos. |
| RNF-03 | Segurança | Consultas parametrizadas | Entrada do usuário nunca concatenada em SQL. |
| RNF-04 | Disponibilidade | ≥ 99% em teste local | Fallback em memória para testes. |
| RNF-05 | Auditoria | 100% das tentativas de consulta registradas | Log com resultado permitido ou negado. |

## 8. Design e Interface

**Componentes afetados:** 🟡 Ferramenta de identificação, ferramenta de pedidos, repositórios de clientes e pedidos, guardrail de privacidade.

**Comportamento esperado:** 🟡 O agente conduz a identificação em etapas curtas, confirma o nome e mostra os dados do pedido em formato de resumo.

**Estados da UI:**
- Estado vazio: 🟡 solicitação de número do pedido e identificação.
- Estado de carregamento: 🟡 indicação de consulta em andamento.
- Estado de erro: 🟡 mensagem de dados divergentes ou pedido não encontrado.
- Estado de sucesso: 🟡 resumo do pedido com status, itens, rastreio e previsão.

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
customers {
  customer_id: int
  name: text
  phone: text
  email: text
  city: text
}

orders {
  order_id: int
  customer_id: int
  order_date: date
  status: text          // pending, confirmed, shipped, delivered, cancelled
  total_brl: numeric
  payment_method: text
  tracking_code: text
  estimated_delivery: date
  notes: text
}

order_items {
  order_id: int
  product_id: int
  quantity: int
}
```

**Migrações necessárias:** 🟡 Sim; criar índices em orders.customer_id, orders.status e order_items.order_id.

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| Supabase Postgres | Obrigatória | Fallback em memória para testes; sem dados, o agente oferece escalonamento. |
| CSV de clientes, pedidos e itens | Obrigatória | Sem ingestão, a consulta retorna erro explícito. |
| Ferramenta de identificação | Obrigatória | Sem identificação, nenhuma consulta de pedido é permitida. |
| LLM com tool calling | Obrigatória | Sem tool call, o agente não afirma status de pedido. |

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: Pedido inexistente | Número não encontrado | Pedir para conferir o número e oferecer escalonamento; não revelar dados de terceiros. |
| EC-02: Identidade divergente | Nome ou contato não confere | Negar a consulta e pedir confirmação; após duas falhas, encaminhar a humano. |
| EC-03: E-mail duplicado | Dois clientes com o mesmo e-mail | Pedir telefone ou nome completo para desambiguar. |
| EC-04: Pedido cancelado | status cancelled | Informar cancelamento e motivo registrado, sem prometer reembolso. |
| EC-05: Pedido sem rastreio | tracking_code vazio | Informar que o rastreio ainda não foi gerado e mostrar o status atual. |
| EC-06: Timeout do banco | Consulta acima de 5 s | Acionar fallback em memória e registrar incidente. |
| EC-07: Data de entrega ausente | estimated_delivery vazio | Informar que a previsão ainda não está disponível. |

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Identificação leve por nome e telefone ou e-mail; sem senha na v1.
- **Autorização:** 🟡 O cliente só acessa pedidos vinculados ao próprio cadastro.
- **Dados sensíveis:** 🟡 Telefone e e-mail são mascarados; o histórico não armazena documentos.
- **Auditoria:** 🟡 Registrar tentativa, resultado permitido ou negado e motivo do escalonamento.

## 13. Plano de Rollout

- **Estratégia:** 🟡 Big bang no protótipo, com feature flag para desligar a consulta de pedidos.
- **Como reverter (rollback):** 🟡 Desativar a ferramenta de pedidos e orientar o cliente a falar com a equipe; restaurar o commit anterior.
- **Monitoramento pós-deploy:** 🟡 Observar tentativas negadas, pedidos não encontrados e tempo P95.

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | Quantas tentativas de identificação são aceitáveis antes do escalonamento? | Médio | adelino | 2026-11-03 |
| OQ-02 | O cliente pode consultar pedidos apenas pelo e-mail, sem telefone? | Baixo | adelino | 2026-11-03 |

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| Identificação por nome e telefone ou e-mail | Login com senha, CPF | Dados disponíveis e menor atrito no protótipo. |
| Consulta somente do próprio pedido | Listar todos os pedidos do cliente | Reduz exposição de dados e simplifica a resposta. |
| Status em linguagem de cliente | Código interno do status | Melhora compreensão sem perder rastreabilidade. |
| Escalonamento após duas falhas | Insistir indefinidamente | Evita frustração e tentativa de engenharia social. |

## Apêndice

### Referências
- PRD em _reversa_sdd/prd.md
- Manual de Políticas da Empório da Música, seções 4 e 5
- CSVs de clientes, pedidos e itens de pedido

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
