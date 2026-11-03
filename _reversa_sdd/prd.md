# PRD: Agente de Atendimento Empório da Música

> Selo 🟡 PLANEJADO. Documento gerado a partir de ideation + personas.

**Versão:** 1.0
**Data:** 2026-11-03T14:26:44Z
**Autor:** reversa-drafter
**Status:** rascunho

---

## 1. Problema

🟡 A equipe da Empório da Música gasta tempo excessivo respondendo perguntas recorrentes sobre horário, preço, disponibilidade, promoções e status de pedido. Os clientes, por sua vez, esperam por informações básicas e nem sempre conseguem atendimento fora do horário comercial. O problema afeta tanto a eficiência operacional da loja quanto a experiência de compra.

### Quem sente

🟡
- **Equipe de atendimento:** sobrecarga com perguntas repetitivas e interrupções durante o dia.
- **Marina (cliente iniciante):** insegurança e demora para descobrir qual instrumento cabe no orçamento.
- **Rafael (músico pós-venda):** falta de previsibilidade sobre pedido, rastreio, troca ou garantia.

---

## 2. Personas-alvo

🟡 Referência completa em [`personas.md`](./personas.md). Resumo:

- **Cliente iniciante (Marina):** 🟡 está comprando o primeiro instrumento, pesquisa pelo celular e precisa de orientação simples, acolhedora e dentro do orçamento.
- **Músico pós-venda (Rafael):** 🟡 já comprou na loja e precisa resolver rapidamente status de pedido, rastreio, troca, defeito ou garantia.

---

## 3. Métricas de sucesso

🟡

| Métrica | Unidade | Alvo | Prazo |
|---|---|---|---|
| Redução de perguntas repetitivas atendidas pela equipe | percentual | 40% | 3 meses após entrada em operação |
| Tempo até a primeira resposta no horário comercial | minutos | até 1 minuto | imediato na v1 |
| Respostas corretas em auditoria amostral | percentual | pelo menos 90% | 3 meses |
| Taxa de escalonamento para humano | percentual de conversas | abaixo de 20% | 3 meses |
| Cobertura de testes automatizados do núcleo | percentual | pelo menos 70% | entrega da v1 |
| Exemplos de conversa entregues | quantidade | 3 a 5 | entrega da v1 |

---

## 4. Escopo (in)

🟡

- 🟡 Chat por mensagens de texto com persona da Empório da Música, tom informal, acolhedor e profissional.
- 🟡 Interface web simples servida pelo FastAPI, com sessão e histórico de conversa.
- 🟡 Persistência de conversas, mensagens, ferramentas chamadas e escalonamentos no Supabase.
- 🟡 Consulta ao catálogo por termo, categoria e faixa de preço, com nome, preço, estoque, status, descrição e especificações.
- 🟡 Consulta de detalhe de produto e de promoções ativas, incluindo regra de PIX e parcelamento.
- 🟡 Identificação leve do cliente e consulta de pedidos próprios: status, itens, rastreio, previsão de entrega e observações.
- 🟡 Consulta às políticas da loja via RAG: horário, endereço, contato, trocas, devoluções, garantia, frete e formas de pagamento.
- 🟡 Aplicação da regra de frete para Campo Grande/MS; fora da região metropolitana, informar que o valor é sob cotação.
- 🟡 Tratamento de perguntas fora do escopo, incluindo acessórios, concorrentes e assuntos não relacionados.
- 🟡 Escalonamento para atendimento humano com registro de motivo e resumo.
- 🟡 Guardrails contra invenção de preço, estoque, prazo e desconto; citação das seções do manual nas respostas de política.
- 🟡 Abstração de provedor de LLM: DeepSeek Flash como padrão, OpenAI `gpt-4o-mini` como fallback e Gemini como alternativa gratuita.
- 🟡 Camada de repositórios com Supabase como fonte principal e implementação em memória para testes e execução offline.
- 🟡 Ingestão e validação dos CSVs, com relatório de qualidade dos dados.
- 🟡 README, testes automatizados e 3 a 5 exemplos de conversa.

---

## 5. Não-objetivos (out)

🟡

- 🟡 Carrinho de compras, criação de pedido real ou checkout.
- 🟡 Processamento de pagamento ou emissão de nota fiscal.
- 🟡 Integração real com WhatsApp, telefonia ou e-mail.
- 🟡 Venda de acessórios como cordas, palhetas, cabos, cases, pedais ou amplificadores.
- 🟡 Recomendação de lojas concorrentes ou comparação de preços externos.
- 🟡 Backoffice de estoque, cadastro de produtos ou gestão de promoções.
- 🟡 Autenticação forte de clientes; a v1 faz identificação leve por número do pedido + nome/telefone/e-mail.
- 🟡 Atendimento multilíngue; a v1 é em português do Brasil.
- 🟡 Fine-tuning de modelo ou treinamento próprio.
- 🟡 Deploy em produção com SLA, observabilidade avançada e alta disponibilidade.

---

## 6. Restrições

🟡

| Tipo | Descrição |
|---|---|
| 🟡 Técnica | 🟡 Python como linguagem principal; FastAPI para API e UI; Supabase Postgres para dados e histórico; interface de repositórios para baixo acoplamento. |
| 🟡 Técnica | 🟡 LLM padrão DeepSeek Flash, com adapters para OpenAI e Gemini; function calling com ferramentas determinísticas e RAG sobre o manual. |
| 🟡 Técnica | 🟡 Sem Docker no ambiente local; o Supabase será remoto e haverá fallback em memória para testes e demonstração. |
| 🟡 Prazo | 🟡 Entrega em 03/11/2026 até 19h (horário local), conforme informado pelo usuário. |
| 🟡 Compliance | 🟡 LGPD: minimização de dados, não exposição de dados de outros clientes, mascaramento de telefone/e-mail em logs e documentação sobre retenção. |
| 🟡 Compliance | 🟡 Dados fictícios do desafio; em produção, seria necessário base legal, contrato com provedor de LLM e política de retenção. |
| 🟡 Orçamento | 🟡 [INDEFINIDO, validar com usuário] — premissa de usar DeepSeek/OpenAI de baixo custo e Gemini free tier apenas em desenvolvimento. |

---

## 7. Dependências externas

🟡

- 🟡 Projeto Supabase com `SUPABASE_DB_URL` e schema aplicado.
- 🟡 Chave da API DeepSeek; opcionalmente OpenAI e Gemini.
- 🟡 CSVs e PDF de políticas fornecidos no repositório.
- 🟡 Bibliotecas Python: FastAPI, Uvicorn, Pydantic, Psycopg, pandas, pdfplumber, httpx e cliente OpenAI-compatível.
- 🟡 Nenhuma dependência de API real de WhatsApp nesta versão.

---

## 8. Riscos

🟡

| Risco | Impacto | Probabilidade | Mitigação proposta |
|---|---|---|---|
| Dados inconsistentes nos CSVs (descrições divergentes, totais diferentes, clientes duplicados, sem CEP) | 🟡 médio | 🟡 alta | 🟡 Validar na ingestão, confiar nos campos estruturados, documentar suposições e não corrigir dados sem aprovação. |
| LLM inventar preço, estoque, prazo ou desconto | 🟡 alto | 🟡 média | 🟡 Ferramentas determinísticas, guardrail que bloqueia resposta sem consulta, testes com LLM scriptado e citações obrigatórias. |
| Prazo curto até 19h | 🟡 alto | 🟡 alta | 🟡 MVP enxuto, fallback local, foco em catálogo/pedidos/políticas, evitar features não essenciais. |
| Credenciais Supabase ou DeepSeek indisponíveis | 🟡 médio | 🟡 média | 🟡 Modo local em memória, `.env.example`, execução de testes sem credenciais e documentação de setup. |
| Vazamento de dados pessoais entre clientes | 🟡 alto | 🟡 baixa | 🟡 Identificação obrigatória, consulta por vínculo do pedido, mascaramento e logs sem PII. |
| Rate limit ou indisponibilidade do provedor LLM | 🟡 médio | 🟡 baixa | 🟡 Retry com backoff, fallback para outro provedor e mensagem amigável de indisponibilidade. |
| Políticas mudarem sem atualização da base | 🟡 médio | 🟡 baixa | 🟡 Versão do manual no índice, citação de seção e rotina de reingestão documentada. |

---

## 9. Critérios de aceite (alto nível)

🟡

- 🟡 **Dado** que Marina pergunta por violões até R$ 1.000, **Quando** o agente consulta o catálogo, **Então** lista produtos reais com preço e disponibilidade, sinaliza itens esgotados e não inventa opções.
- 🟡 **Dado** que Marina pergunta horário, endereço ou formas de pagamento, **Quando** o agente responde, **Então** usa o manual de políticas e cita a seção consultada.
- 🟡 **Dado** que Rafael informa o número do pedido e se identifica, **Quando** o agente consulta, **Então** mostra somente os dados do pedido dele, com status, rastreio e previsão.
- 🟡 **Dado** que Rafael pede devolução ou troca, **Quando** o agente aplica a política, **Então** calcula o prazo com base na data de recebimento, explica as condições e encaminha para humano quando necessário.
- 🟡 **Dado** que o cliente pede um acessório ou assunto fora do escopo, **Quando** o agente responde, **Então** recusa com educação e redireciona sem inventar disponibilidade.
- 🟡 **Dado** que o sistema é executado, **Quando** os testes rodam, **Então** o núcleo passa sem depender de credenciais externas e os exemplos cobrem catálogo, pedido, política, fora de escopo e privacidade.

---

## Pendências de cobertura

🟡
- Orçamento do projeto não informado; registrar premissa de baixo custo.
- Credenciais do Supabase e DeepSeek ainda precisam ser configuradas no `.env` local.
- Confirmar se o prazo de 03/11/2026 até 19h é horário local (America/Campo_Grande).

---

Gerado por reversa-drafter em 2026-11-03T14:26:44Z
Fontes: ideation.md, personas.md
