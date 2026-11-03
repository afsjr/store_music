# Requirements: Agente de Atendimento Empório da Música — MVP

> Identificador: `001-atendimento-mvp`
> Data: `2026-11-03`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

🟡 Entregar um agente de atendimento por mensagens de texto para clientes da Empório da Música. O agente assume a persona da loja, consulta catálogo, promoções, pedidos e políticas, e encaminha casos sensíveis para atendimento humano. A feature resolve a sobrecarga da equipe com perguntas repetitivas e melhora a experiência de pré-venda e pós-venda.

## 2. Contexto a partir do legado

🟡 O projeto é greenfield. As fontes de contexto são o PRD e as seis specs SDD geradas pelo Reversa, além dos CSVs e do manual de políticas fornecidos no desafio.

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/prd.md#4-escopo-in` | Escopo do MVP: chat, catálogo, pedidos, políticas, frete, guardrails, persistência e UI. | 🟡 |
| `_reversa_sdd/prd.md#5-não-objetivos-out` | Carrinho, pagamento, WhatsApp real, acessórios e backoffice ficam fora da v1. | 🟡 |
| `_reversa_sdd/personas.md#persona-1-cliente-iniciante-marina` | Marina busca o primeiro instrumento e precisa de orientação dentro do orçamento. | 🟡 |
| `_reversa_sdd/personas.md#persona-2-músico-pós-venda-rafael` | Rafael precisa resolver pedido, rastreio, troca ou garantia com previsibilidade. | 🟡 |
| `_reversa_sdd/sdd/conversa-atendimento.md#6-requisitos-funcionais` | Loop de conversa, persona, memória, guardrails e escalonamento. | 🟡 |
| `_reversa_sdd/sdd/catalogo-promocoes.md#6-requisitos-funcionais` | Busca, filtros, estoque, preço, promoções, PIX e parcelamento. | 🟡 |
| `_reversa_sdd/sdd/pedidos-clientes.md#6-requisitos-funcionais` | Identificação leve, consulta de pedidos e privacidade. | 🟡 |
| `_reversa_sdd/sdd/politicas-frete.md#6-requisitos-funcionais` | RAG do manual, citações, prazos, horário, endereço e frete. | 🟡 |
| `_reversa_sdd/sdd/plataforma-dados.md#6-requisitos-funcionais` | Schema, ingestão, validação, repositórios e fallback local. | 🟡 |
| `_reversa_sdd/sdd/api-ui.md#6-requisitos-funcionais` | API de chat, UI, sessão, histórico e health check. | 🟡 |
| `emporio_musica/data/desafio_tecnico_ai_eng - products.csv` | 65 produtos, 62 ativos, 2 descontinuados e 1 coming_soon. | 🟢 |
| `emporio_musica/data/desafio_tecnico_ai_eng - orders.csv` | 20 pedidos com status delivered, shipped, confirmed, pending e cancelled. | 🟢 |
| `emporio_musica/data/desafio_tecnico_ai_eng - promotions.csv` | 4 promoções ativas na base. | 🟢 |
| `emporio_musica/data/políticas_da_loja.pdf` | Manual de políticas versão 2.1, com regras de troca, devolução, frete, garantia e atendimento. | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Marina, cliente iniciante | Escolher o primeiro instrumento dentro do orçamento | Pergunta por violões até R$ 1.000 e recebe opções reais com preço e disponibilidade. |
| Rafael, músico pós-venda | Resolver pedido, rastreio, troca ou garantia | Informa o pedido, se identifica e recebe status e previsão somente do próprio pedido. |
| Equipe de atendimento | Reduzir perguntas repetitivas e receber casos complexos | Consulta o histórico e recebe escalonamentos com motivo e resumo. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 O agente deve assumir tom informal, acolhedor e profissional, conforme o manual de atendimento.
   - Origem: `_reversa_sdd/sdd/conversa-atendimento.md#6-requisitos-funcionais`
   - Tipo: nova
2. **RN-02:** 🟡 Preço, estoque, promoção, frete e status de pedido só podem ser afirmados após consulta à ferramenta correspondente.
   - Origem: `_reversa_sdd/sdd/conversa-atendimento.md#6-requisitos-funcionais`
   - Tipo: nova
3. **RN-03:** 🟡 A loja comercializa somente instrumentos musicais; acessórios devem ser recusados com redirecionamento educado.
   - Origem: `_reversa_sdd/prd.md#5-não-objetivos-out`
   - Tipo: nova
4. **RN-04:** 🟡 Promoções não são cumulativas e o desconto de PIX de 5% não se aplica sobre preço promocional.
   - Origem: `_reversa_sdd/sdd/catalogo-promocoes.md#6-requisitos-funcionais`
   - Tipo: nova
5. **RN-05:** 🟡 Produto ativo com estoque zero está indisponível temporariamente; descontinuado saiu do catálogo; coming_soon ainda não está à venda.
   - Origem: `_reversa_sdd/sdd/catalogo-promocoes.md#6-requisitos-funcionais`
   - Tipo: nova
6. **RN-06:** 🟡 O cliente só pode consultar pedidos vinculados ao próprio cadastro, após identificação por nome e telefone ou e-mail.
   - Origem: `_reversa_sdd/sdd/pedidos-clientes.md#6-requisitos-funcionais`
   - Tipo: nova
7. **RN-07:** 🟡 O prazo de arrependimento é de 7 dias corridos após o recebimento; troca por defeito é de 30 dias após a compra; garantia legal é de 90 dias.
   - Origem: `_reversa_sdd/sdd/politicas-frete.md#6-requisitos-funcionais`
   - Tipo: nova
8. **RN-08:** 🟡 Frete é grátis acima de R$ 500 em Campo Grande; abaixo disso, taxa fixa de R$ 35; outras cidades dependem de cotação por CEP, peso e dimensões.
   - Origem: `_reversa_sdd/sdd/politicas-frete.md#6-requisitos-funcionais`
   - Tipo: nova
9. **RN-09:** 🟡 Toda resposta baseada em política deve citar a seção e a página do manual.
   - Origem: `_reversa_sdd/sdd/politicas-frete.md#6-requisitos-funcionais`
   - Tipo: nova
10. **RN-10:** 🟡 Reclamações, dúvidas sem resposta e pedidos explícitos de humano devem gerar escalonamento com motivo e resumo.
    - Origem: `_reversa_sdd/sdd/conversa-atendimento.md#6-requisitos-funcionais`
    - Tipo: nova
11. **RN-11:** 🟡 O agente não pode prometer desconto expirado, reserva de preço ou condição fora do manual.
    - Origem: `_reversa_sdd/sdd/politicas-frete.md#6-requisitos-funcionais`
    - Tipo: nova
12. **RN-12:** 🟡 A data de referência para prazos é configurável, com padrão na data real do sistema.
    - Origem: `_reversa_sdd/prd.md#6-restrições`
    - Tipo: nova
13. **RN-13:** 🟡 O agente deve recusar assuntos fora do escopo da loja e não compartilhar dados de outros clientes.
    - Origem: `_reversa_sdd/sdd/conversa-atendimento.md#12-segurança-e-privacidade`
    - Tipo: nova
14. **RN-14:** 🟡 O histórico da conversa deve ser persistido e limitado às últimas 12 mensagens no contexto ativo.
    - Origem: `_reversa_sdd/sdd/conversa-atendimento.md#6-requisitos-funcionais`
    - Tipo: nova
15. **RN-15:** 🟡 A loja não cria pedido, não processa pagamento e não altera estoque nesta versão.
    - Origem: `_reversa_sdd/prd.md#5-não-objetivos-out`
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve responder com a persona da Empório da Música, usando tom informal, acolhedor e profissional. | Must | Auditoria de 10 respostas confirma o tom definido no manual. | 🟡 |
| RF-02 | O sistema deve persistir mensagens do usuário, do assistente e chamadas de ferramentas no histórico da sessão. | Must | Consulta ao histórico retorna as mensagens em ordem cronológica. | 🟡 |
| RF-03 | O sistema deve usar as últimas 12 mensagens como contexto ativo da conversa. | Must | Teste com 20 mensagens confirma que apenas 12 entram no prompt. | 🟡 |
| RF-04 | O sistema deve executar ferramenta antes de afirmar preço, estoque, promoção, frete ou status de pedido. | Must | Resposta com valor em reais sem tool call é bloqueada. | 🟡 |
| RF-05 | O sistema deve buscar produtos por termo, categoria e faixa de preço. | Must | Busca por violões até R$ 1.000 retorna somente produtos da categoria 5 dentro do limite. | 🟡 |
| RF-06 | O sistema deve retornar até 10 produtos por consulta e informar quando houver mais resultados. | Must | Busca ampla retorna 10 itens e uma mensagem de refino. | 🟡 |
| RF-07 | O sistema deve informar preço de tabela, promoção ativa, preço promocional, estoque e status do produto. | Must | Produto 127 retorna desconto ativo de 10%; produto 95 retorna preço de tabela e PIX de 5%. | 🟡 |
| RF-08 | O sistema deve sinalizar produtos esgotados, descontinuados e coming_soon de forma explícita. | Must | Produto 96 retorna indisponível; produto 113 retorna descontinuado; produto 130 retorna coming_soon. | 🟡 |
| RF-09 | O sistema deve solicitar número do pedido e identificação do cliente antes de consultar pedidos. | Must | Consulta sem identificação retorna pedido de nome e telefone ou e-mail. | 🟡 |
| RF-10 | O sistema deve validar o vínculo entre cliente e pedido e retornar somente pedidos do próprio cliente. | Must | Tentativa de consultar pedido de outro cliente é negada sem revelar dados. | 🟡 |
| RF-11 | O sistema deve retornar status, itens, total, rastreio e previsão de entrega do pedido. | Must | Pedido 8 retorna status shipped, itens e rastreio BRJL5544332BR. | 🟡 |
| RF-12 | O sistema deve responder dúvidas de política com trechos recuperados do manual e citação de seção e página. | Must | Pergunta sobre devolução cita a seção 4.1 e a página correspondente. | 🟡 |
| RF-13 | O sistema deve calcular prazos de arrependimento, defeito e garantia com base nas datas aplicáveis. | Must | Pedido entregue em 2026-02-17 e consulta em 2026-02-20 retorna 3 dias corridos. | 🟡 |
| RF-14 | O sistema deve informar a regra de frete para Campo Grande e indicar cotação para outras cidades. | Must | Compra de R$ 600 em Campo Grande retorna frete grátis; R$ 400 retorna R$ 35; outra cidade retorna sob cotação. | 🟡 |
| RF-15 | O sistema deve informar horário, endereço, telefone e e-mail da loja a partir do manual. | Must | Resposta retorna horário de segunda a sexta, sábado, domingo e endereço completo. | 🟡 |
| RF-16 | O sistema deve recusar perguntas fora do escopo com redirecionamento educado. | Must | Pergunta sobre cordas recebe recusa e sugestão de loja parceira, sem preço inventado. | 🟡 |
| RF-17 | O sistema deve registrar escalonamento com motivo, resumo e status. | Must | Pedido de humano cria registro com status aberto. | 🟡 |
| RF-18 | O sistema deve usar provedor alternativo quando o LLM principal falhar. | Should | Erro 503 no provedor principal aciona fallback e resposta amigável. | 🟡 |
| RF-19 | O sistema deve expor chat, sessão, histórico e health check em interface web e API. | Must | UI envia mensagem, recebe resposta e health retorna 200 quando configurado. | 🟡 |
| RF-20 | O sistema deve ingerir os CSVs com validação e gerar relatório de qualidade dos dados. | Must | Ingestão idempotente mantém contagens 9, 65, 50, 20, 22 e 25; relatório lista inconsistências. | 🟡 |
| RF-21 | O sistema deve operar em modo local em memória quando o banco não estiver disponível. | Should | Testes sem credenciais consultam produto 95 e pedido 8 com sucesso. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | O tempo de resposta final do chat deve ser de no máximo 8 segundos para P95. | `_reversa_sdd/sdd/conversa-atendimento.md#7-requisitos-não-funcionais` | 🟡 |
| Desempenho | Consultas de catálogo e pedido devem responder em no máximo 2 segundos para P95. | `_reversa_sdd/sdd/catalogo-promocoes.md#7-requisitos-não-funcionais` | 🟡 |
| Segurança | Consultas ao banco devem usar parâmetros e nunca concatenar entrada do usuário. | `_reversa_sdd/sdd/plataforma-dados.md#6-requisitos-funcionais` | 🟡 |
| Segurança | Telefone e e-mail devem ser mascarados em logs e respostas de depuração. | `_reversa_sdd/sdd/conversa-atendimento.md#12-segurança-e-privacidade` | 🟡 |
| Privacidade | O agente não deve revelar dados de outro cliente, mesmo com número de pedido válido. | `_reversa_sdd/sdd/pedidos-clientes.md#12-segurança-e-privacidade` | 🟡 |
| Observabilidade | Toda requisição deve ter request_id e registrar latência, ferramentas chamadas e status. | `_reversa_sdd/sdd/api-ui.md#7-requisitos-não-funcionais` | 🟡 |
| Confiabilidade | O sistema deve aplicar retry com backoff e fallback de provedor em falhas externas. | `_reversa_sdd/sdd/conversa-atendimento.md#11-edge-cases-e-tratamento-de-erros` | 🟡 |
| Acessibilidade | A UI deve permitir navegação por teclado e ter rótulos ARIA no campo de mensagem e envio. | `_reversa_sdd/sdd/api-ui.md#7-requisitos-não-funcionais` | 🟡 |
| Manutenibilidade | O domínio deve depender de interfaces de repositório e de LLM, sem acoplamento a fornecedores. | `_reversa_sdd/sdd/plataforma-dados.md#15-decisões-tomadas-decision-log` | 🟡 |
| Conformidade | A v1 usa dados fictícios; em produção, deve haver base legal e retenção definida para LGPD. | `_reversa_sdd/prd.md#6-restrições` | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Busca de violões dentro do orçamento
  Dado que Marina pergunta por violões custando até R$ 1.000
  Quando o agente consulta o catálogo
  Então a resposta lista apenas produtos reais dentro do limite
  E informa preço e disponibilidade de cada opção

Cenário: Produto esgotado
  Dado que o produto consultado está ativo e com estoque zero
  Quando o agente responde sobre a disponibilidade
  Então informa que o produto está temporariamente indisponível
  E sugere alternativa semelhante sem inventar estoque

Cenário: Preço com promoção e PIX
  Dado que o produto 127 tem promoção ativa de 10%
  Quando o cliente pergunta o preço final
  Então o agente mostra o preço de tabela, o desconto e o preço promocional
  E não aplica o desconto de PIX sobre o preço promocional

Cenário: Consulta de pedido com identificação
  Dado que Rafael informa o pedido 8 e se identifica corretamente
  Quando o agente valida o vínculo
  Então retorna status, itens, rastreio e previsão do pedido 8
  E mascara telefone e e-mail na resposta

Cenário: Tentativa de consultar pedido de outro cliente
  Dado que o cliente informa um pedido que não pertence ao seu cadastro
  Quando o agente valida a identidade
  Então nega a consulta sem revelar dados
  E oferece escalonamento humano após duas tentativas

Cenário: Devolução dentro do prazo
  Dado que o pedido foi recebido há 3 dias corridos
  Quando o cliente pergunta se pode devolver
  Então o agente aplica a regra de 7 dias
  E cita a seção do manual que sustenta a resposta

Cenário: Pergunta fora do escopo
  Dado que o cliente pergunta sobre cordas de violão
  Quando o agente identifica que a loja não vende acessórios
  Então recusa com educação e redireciona
  E não consulta preço de acessório

Cenário: Falha do provedor de LLM
  Dado que o provedor principal retorna erro 503
  Quando o agente tenta responder
  Então aciona o provedor alternativo
  E, se ambos falharem, responde com aviso de indisponibilidade e registra o incidente
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-17 | Must | Cobrem persona, catálogo, pedidos, políticas, frete e guardrails, que são o núcleo do desafio. |
| RF-18 | Should | Fallback aumenta disponibilidade, mas o MVP funciona com um provedor. |
| RF-19 | Must | A entrega exige interface demonstrável e health check. |
| RF-20 | Must | Sem ingestão validada, os dados não são confiáveis. |
| RF-21 | Should | Fallback local garante testes e demonstração sem credenciais. |
| Benchmark de provedores | Could | Ajuda a comparar custo e confiabilidade, mas não bloqueia o MVP. |
| Stream de respostas | Could | Melhora a experiência, mas a resposta completa atende ao prazo. |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Não há pontos em aberto neste documento.

## 10. Lacunas

Nenhuma lacuna identificada. As decisões de stack, escopo e dados estão registradas no PRD e nas specs SDD. O orçamento permanece como premissa de baixo custo.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-03 | Versão inicial gerada por `/reversa-requirements` | reversa |
