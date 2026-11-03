# Spec: Plataforma de Dados

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-11-03
**Reviewers:** N/A

---

## 1. Resumo

🟡 A feature cobre o schema do Supabase, a ingestão e validação dos CSVs, os repositórios de acesso e o fallback em memória para testes e execução offline. Ela existe para que o agente consulte dados confiáveis com baixo acoplamento e sem depender de credenciais em todos os ambientes.

## 2. Contexto e Motivação

**Problema:** 🟡 Os dados chegam em CSVs com inconsistências, e o agente precisa de consultas parametrizadas, idempotentes e testáveis. Sem uma camada de dados bem definida, o domínio fica acoplado ao Supabase e difícil de testar.

**Evidências:** 🟡 Existem 65 produtos, 50 clientes, 20 pedidos, 22 itens e 25 promoções. Há descrições divergentes, totais diferentes da soma dos itens, e-mail duplicado e ausência de CEP nos clientes.

**Por que agora:** 🟡 O prazo de entrega é 03/11/2026 até 19h; a ingestão precisa ser reproduzível e o fallback local precisa permitir testar sem Supabase.

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 Criar schema e migrations idempotentes no Supabase.
- [ ] G-02: 🟡 Ingerir os seis CSVs com validação de PK, FK, status e valores.
- [ ] G-03: 🟡 Expor repositórios com interfaces para catálogo, pedidos, clientes, promoções e conversas.
- [ ] G-04: 🟡 Permitir execução local em memória a partir dos mesmos CSVs.
- [ ] G-05: 🟡 Gerar relatório de qualidade dos dados com as inconsistências encontradas.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Ingestão idempotente | não medido | 2 execuções com as mesmas contagens | 2026-11-03 |
| Violações de FK após validação | não medido | 0 | 2026-11-03 |
| Cobertura de testes dos repositórios | 0% | ≥ 70% | 2026-11-03 |
| Tempo de ingestão completa | não medido | ≤ 60 s | 2026-11-03 |

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Não haverá escrita de volta nos CSVs originais.
- NG-02: 🟡 Não haverá backoffice de cadastro, edição ou exclusão de produtos.
- NG-03: 🟡 Não haverá sincronização em tempo real com sistemas externos.
- NG-04: 🟡 Não haverá multi-tenant nem separação por loja nesta versão.
- NG-05: 🟡 Não haverá correção automática de descrições divergentes dos produtos.

## 5. Usuários e Personas

**Usuário primário:** 🟡 Equipe técnica que executa a ingestão e mantém o schema.

**Usuário secundário:** 🟡 Agente e serviços de domínio que consomem os repositórios.

**Jornada atual (sem a feature):** 🟡 Dados em CSV são lidos diretamente por scripts, sem validação nem contrato de acesso.

**Jornada futura (com a feature):** 🟡 A equipe roda a ingestão, recebe o relatório de qualidade e o agente consulta repositórios com contratos estáveis.

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve criar as tabelas categories, products, customers, orders, order_items, promotions, conversations, messages e handoffs. | Must | Script de migration aplica o schema em banco vazio sem erro. |
| RF-02 | O sistema deve validar unicidade de chaves primárias e integridade de chaves estrangeiras. | Must | Ingestão com FK inválida falha e lista o registro problemático. |
| RF-03 | O sistema deve normalizar textos, datas, números e o campo specs em JSON. | Must | Produto 81 é gravado com specs em JSON válido e created_at como data. |
| RF-04 | O sistema deve fazer upsert idempotente na ordem categories, products, customers, orders, order_items e promotions. | Must | Duas execuções seguidas mantêm as contagens 9, 65, 50, 20, 22 e 25. |
| RF-05 | O sistema deve validar status permitidos de produto e pedido. | Must | Status fora da lista é rejeitado com mensagem clara. |
| RF-06 | O sistema deve validar preço, estoque e quantidade como valores não negativos. | Must | Valor negativo é rejeitado e não gravado. |
| RF-07 | O sistema deve gerar relatório de qualidade com descrições divergentes, totais diferentes e e-mails duplicados. | Must | Relatório lista os pedidos 3 e 20 e os clientes 11 e 43. |
| RF-08 | O sistema deve oferecer repositórios em memória carregados dos CSVs. | Must | Teste sem Supabase consulta produto 95 e pedido 8 com sucesso. |
| RF-09 | O sistema deve usar consultas parametrizadas em todos os acessos ao banco. | Must | Revisão de código não encontra concatenação de entrada em SQL. |
| RF-10 | O sistema deve registrar data e versão da ingestão. | Should | Tabela de controle retorna a última execução e o número de registros. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 A equipe configura a conexão do Supabase no arquivo de ambiente.
2. 🟡 O sistema lê os seis arquivos CSV do diretório de dados.
3. 🟡 O sistema normaliza e valida os registros.
4. 🟡 O sistema aplica upsert na ordem de dependência.
5. 🟡 O sistema gera o relatório de qualidade dos dados.
6. 🟡 O sistema exibe as contagens e eventuais inconsistências.
7. 🟡 Resultado: o banco fica pronto para consultas do agente.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — CSV ausente:**
1. 🟡 O sistema interrompe a ingestão antes de gravar qualquer registro.
2. 🟡 O sistema informa o arquivo ausente e o caminho esperado.
3. 🟡 O sistema não executa ingestão parcial.

**Fluxo Alternativo B — Banco indisponível:**
1. 🟡 A conexão com o Supabase falha ou expira.
2. 🟡 O sistema tenta reconectar uma vez e registra o erro.
3. 🟡 O sistema orienta usar o modo local em memória.

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Tempo de ingestão | ≤ 60 s | Para os seis CSVs do desafio. |
| RNF-02 | Idempotência | 2 execuções sem duplicar registros | Upsert com chave primária. |
| RNF-03 | Segurança | Credenciais apenas em variáveis de ambiente | Nenhum segredo no repositório. |
| RNF-04 | Integridade | 0 violações de FK ao final | Validação antes da escrita. |
| RNF-05 | Observabilidade | 100% das execuções registradas | Data, contagens e erros. |

## 8. Design e Interface

**Componentes afetados:** 🟡 Migrations SQL, script de ingestão, repositórios Supabase, repositórios em memória, relatório de qualidade e configuração de ambiente.

**Comportamento esperado:** 🟡 A ingestão exibe progresso por arquivo, contagens e um resumo final com avisos de qualidade. O modo local é ativado por variável de ambiente.

**Estados da UI:**
- Estado vazio: 🟡 aviso de diretório de dados sem CSVs.
- Estado de carregamento: 🟡 progresso por arquivo durante a ingestão.
- Estado de erro: 🟡 lista de registros inválidos e instrução de correção.
- Estado de sucesso: 🟡 contagens finais e caminho do relatório de qualidade.

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
categories {
  category_id: int
  name: text
  description: text
}

products {
  product_id: int
  name: text
  price_brl: numeric
  category_id: int
  description: text
  stock_quantity: int
  status: text
  specs: jsonb
  created_at: date
  search_vector: tsvector
}

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
  status: text
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

promotions {
  promotion_id: int
  product_id: int
  discount_percent: numeric
  description: text
  is_active: boolean
}

ingestion_runs {
  id: uuid
  started_at: timestamp
  finished_at: timestamp
  status: text
  counts: jsonb
  report_path: text
}
```

**Migrações necessárias:** 🟡 Sim; criar todas as tabelas, índices, a view product_offers e a extensão de busca textual.

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| Supabase Postgres | Obrigatória em produção | Fallback em memória para testes e demonstração. |
| CSVs de entrada | Obrigatória | Sem arquivos, a ingestão não inicia. |
| pandas e psycopg | Obrigatória | Sem bibliotecas, a ingestão não executa. |
| pdfplumber | Opcional | Usado apenas para o índice de políticas. |

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: CSV ausente | Arquivo esperado não existe | Abortar antes de escrever e informar o caminho ausente. |
| EC-02: FK inválida | Pedido referencia cliente inexistente | Rejeitar o registro e listar pedido e cliente na validação. |
| EC-03: PK duplicada | Dois registros com o mesmo ID | Manter o último registro e reportar a duplicidade. |
| EC-04: JSON de specs inválido | Campo specs não é JSON válido | Rejeitar o produto e reportar a linha. |
| EC-05: Banco indisponível | Timeout de conexão | Tentar reconectar uma vez e orientar o modo local. |
| EC-06: Encoding inválido | Arquivo fora de UTF-8 | Ler com fallback e reportar o encoding detectado. |
| EC-07: Ingestão parcial | Falha no meio do processo | Usar transação por arquivo e registrar o ponto de falha. |

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 A ingestão usa credenciais de backend em variáveis de ambiente.
- **Autorização:** 🟡 Apenas o processo de ingestão e o backend acessam o banco.
- **Dados sensíveis:** 🟡 Telefone e e-mail são armazenados por necessidade de atendimento; logs não exibem valores completos.
- **Auditoria:** 🟡 Registrar cada execução de ingestão com data, contagens e status.

## 13. Plano de Rollout

- **Estratégia:** 🟡 Executar migrations e ingestão em ambiente de teste antes do uso pelo agente.
- **Como reverter (rollback):** 🟡 Restaurar backup do banco ou recriar o schema; desativar o modo Supabase e usar memória.
- **Monitoramento pós-deploy:** 🟡 Verificar contagens, violações de FK, tempo de ingestão e erros de conexão.

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | Qual política de retenção para conversas e mensagens no Supabase? | Médio | adelino | 2026-11-03 |
| OQ-02 | O relatório de qualidade deve bloquear a ingestão ou apenas avisar? | Médio | adelino | 2026-11-03 |

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| Supabase como fonte principal | SQLite local como principal | Atende ao requisito do usuário e permite consultas SQL completas. |
| Repositórios com interfaces | Acesso direto ao banco nos serviços | Mantém baixo acoplamento e testabilidade. |
| Fallback em memória | Docker com Supabase local | Docker não está disponível no ambiente. |
| Upsert idempotente | Truncate e reload | Permite reexecução segura sem perder dados. |

## Apêndice

### Referências
- PRD em _reversa_sdd/prd.md
- CSVs em emporio_musica/data
- Manual de Políticas da Empório da Música, seção 9

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
