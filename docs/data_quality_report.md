# Relatório de Qualidade dos Dados

**Data:** 2026-11-03
**Diretório:** `emporio_musica/data`

## Contagens

| Arquivo | Registros |
|---|---:|
| categories | 9 |
| products | 65 |
| customers | 50 |
| orders | 20 |
| order_items | 22 |
| promotions | 25 |

## Ocorrências

| Severidade | Categoria | Descrição |
|---|---|---|
| aviso | duplicidade | E-mails duplicados: 11 (bruno.martins@jmail.com), 43 (bruno.martins@jmail.com) |
| aviso | estoque | Produtos ativos com estoque zero: 96 |
| aviso | total | Pedido 3: total cobrado 3450.00 difere da soma dos itens 3498.00. |
| aviso | total | Pedido 20: total cobrado 1400.00 difere da soma dos itens 1488.00. |
| info | descricao | Produto 135 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 136 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 137 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 138 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 139 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 140 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 141 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 142 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 143 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | descricao | Produto 144 possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica. |
| info | promocao | Promoções ativas: 127 (10%), 121 (20%), 90 (18%), 94 (8%) |

## Suposições de tratamento

- Campos estruturados (`name`, `price_brl`, `stock_quantity`, `status`) prevalecem sobre descrições.
- `is_active` indica promoção vigente; não há data de validade no CSV.
- Produto ativo com estoque zero é tratado como indisponível temporariamente.
- `orders.total_brl` é o valor cobrado, mesmo quando difere da soma dos itens.
- E-mails duplicados não são mesclados.
- Clientes não têm CEP; frete fora da região metropolitana fica sob cotação.
