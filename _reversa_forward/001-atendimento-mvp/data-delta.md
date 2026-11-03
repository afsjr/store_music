# Data Delta: Agente de Atendimento Empório da Música — MVP

> Identificador: `001-atendimento-mvp`
> Data: `2026-11-03`
> Modelo de origem: greenfield com CSVs do desafio
> Detalhe do roadmap: `_reversa_forward/001-atendimento-mvp/roadmap.md#6-delta-no-modelo-de-dados`

## 1. Visão geral

🟡 O projeto não tem modelo de dados legado. O delta cria o modelo operacional a partir dos seis CSVs e acrescenta tabelas de atendimento, políticas e controle de ingestão.

## 2. Entidades de domínio

### 2.1 categories

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| category_id | integer | PK | CSV categories |
| name | text | not null | CSV categories |
| description | text | not null | CSV categories |

### 2.2 products

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| product_id | integer | PK | CSV products |
| name | text | not null | CSV products |
| price_brl | numeric(10,2) | >= 0 | CSV products |
| category_id | integer | FK categories | CSV products |
| description | text | not null | CSV products |
| stock_quantity | integer | >= 0 | CSV products |
| status | text | active, discontinued, coming_soon | CSV products |
| specs | jsonb | default '{}' | CSV products |
| created_at | date | not null | CSV products |
| search_vector | tsvector | gerado | Derivado de name, description e specs |

### 2.3 customers

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| customer_id | integer | PK | CSV customers |
| name | text | not null | CSV customers |
| phone | text | not null | CSV customers |
| email | text | not null | CSV customers |
| city | text | not null | CSV customers |

### 2.4 orders

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| order_id | integer | PK | CSV orders |
| customer_id | integer | FK customers | CSV orders |
| order_date | date | not null | CSV orders |
| status | text | pending, confirmed, shipped, delivered, cancelled | CSV orders |
| total_brl | numeric(10,2) | >= 0 | CSV orders |
| payment_method | text | not null | CSV orders |
| tracking_code | text | nullable | CSV orders |
| estimated_delivery | date | nullable | CSV orders |
| notes | text | nullable | CSV orders |

### 2.5 order_items

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| order_id | integer | PK composta, FK orders | CSV order_items |
| product_id | integer | PK composta, FK products | CSV order_items |
| quantity | integer | > 0 | CSV order_items |

### 2.6 promotions

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| promotion_id | integer | PK | CSV promotions |
| product_id | integer | FK products | CSV promotions |
| discount_percent | numeric(5,2) | entre 0 e 100 | CSV promotions |
| description | text | not null | CSV promotions |
| is_active | boolean | not null | CSV promotions |

## 3. Entidades de atendimento

### 3.1 conversations

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| id | uuid | PK | Nova |
| session_id | text | not null, index | Nova |
| customer_id | integer | FK customers, nullable | Nova |
| created_at | timestamptz | default now() | Nova |
| updated_at | timestamptz | default now() | Nova |

### 3.2 messages

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| id | bigserial | PK | Nova |
| conversation_id | uuid | FK conversations | Nova |
| role | text | user, assistant, tool, system | Nova |
| content | text | not null | Nova |
| tool_calls | jsonb | default '[]' | Nova |
| citations | jsonb | default '[]' | Nova |
| created_at | timestamptz | default now() | Nova |

### 3.3 handoffs

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| id | uuid | PK | Nova |
| conversation_id | uuid | FK conversations | Nova |
| reason | text | not null | Nova |
| summary | text | not null | Nova |
| status | text | aberto, em_atendimento, resolvido | Nova |
| created_at | timestamptz | default now() | Nova |
| resolved_at | timestamptz | nullable | Nova |

## 4. Entidades de políticas

### 4.1 policy_documents

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| id | uuid | PK | Nova |
| title | text | not null | PDF |
| version | text | not null | PDF |
| source_path | text | not null | PDF |
| indexed_at | timestamptz | not null | Nova |

### 4.2 policy_chunks

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| id | uuid | PK | Nova |
| document_id | uuid | FK policy_documents | Nova |
| section | text | not null | PDF |
| page | integer | not null | PDF |
| content | text | not null | PDF |
| tokens | integer | >= 0 | Derivado |

### 4.3 store_info

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| key | text | PK | Manual |
| value | text | not null | Manual |
| source_section | text | not null | Manual |
| source_page | integer | not null | Manual |

## 5. Controle de ingestão

### 5.1 ingestion_runs

| Campo | Tipo | Restrição | Origem |
|-------|------|-----------|--------|
| id | uuid | PK | Nova |
| started_at | timestamptz | not null | Nova |
| finished_at | timestamptz | nullable | Nova |
| status | text | running, success, failed | Nova |
| counts | jsonb | default '{}' | Nova |
| report_path | text | nullable | Nova |

## 6. View e índices

- 🟡 `product_offers`: junta products e a promoção ativa de maior desconto, calculando preço efetivo.
- 🟡 Índices: products(category_id), products(price_brl), products(status), products(stock_quantity), orders(customer_id), orders(status), order_items(order_id), messages(conversation_id, created_at), conversations(session_id).
- 🟡 GIN em products.search_vector e índice trigram em products.name para busca tolerante a acentos.
- 🟡 Extensões: pg_trgm e unaccent.

## 7. Migrações necessárias

1. 🟡 Criar extensões pg_trgm e unaccent.
2. 🟡 Criar as tabelas na ordem de dependência.
3. 🟡 Criar a view product_offers.
4. 🟡 Criar índices e a coluna search_vector.
5. 🟡 Executar a ingestão em transação por arquivo.
6. 🟡 Registrar a execução em ingestion_runs.

## 8. Tratamento de dados e suposições

- 🟢 O arquivo `products.csv` tem 65 registros; `customers.csv` tem 50; `orders.csv` tem 20; `order_items.csv` tem 22; `promotions.csv` tem 25; `categories.csv` tem 9.
- 🟡 Descrições divergentes de nomes em parte dos produtos 135 a 144 serão preservadas; a fonte canônica é o campo `name`.
- 🟡 Totais dos pedidos 3 e 20 divergem da soma dos itens; o valor de `orders.total_brl` será tratado como valor cobrado.
- 🟡 Promoções sem data de validade usam `is_active` como indicador de vigência.
- 🟡 Produto ativo com estoque zero significa indisponibilidade temporária.
- 🟡 E-mails duplicados entre clientes 11 e 43 não serão mesclados; a identificação pode pedir desambiguação.
- 🟡 Clientes não têm CEP; frete fora da região metropolitana fica sob cotação.
- 🟡 O campo `specs` é JSON e deve ser normalizado antes da gravação.
- 🟡 Datas serão tratadas como `date`; timestamps de conversa usam `timestamptz`.

## 9. Rollback de dados

🟡 Em caso de falha, a ingestão usa transação por arquivo e registra o ponto de falha. Para reverter, restaurar backup do banco ou recriar o schema e executar a ingestão novamente. O modo local em memória permanece disponível.

## 10. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-03 | Versão inicial gerada por `/reversa-plan` | reversa |
