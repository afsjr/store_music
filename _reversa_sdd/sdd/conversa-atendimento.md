# Spec: Conversa e Atendimento

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-11-03
**Reviewers:** N/A

---

## 1. Resumo

🟡 A feature define o loop de conversa do agente de atendimento: receber a mensagem, carregar persona e memória, decidir se consulta ferramentas, responder e registrar o histórico. Ela existe para garantir respostas consistentes com o tom da loja e com as regras de negócio.

## 2. Contexto e Motivação

**Problema:** 🟡 O atendimento atual é manual e a equipe responde perguntas repetitivas. Um agente sem loop estruturado pode inventar preço, estoque ou prazo e gerar frustração.

**Evidências:** 🟡 O manual exige tom informal e profissional, consulta ao sistema antes de informar preço e escalonamento em casos sensíveis. As personas Marina e Rafael precisam de respostas rápidas e confiáveis.

**Por que agora:** 🟡 O desafio exige um protótipo funcional de atendimento por mensagens, com prazo de entrega em 03/11/2026 até 19h.

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 Responder mensagens com a persona da Empório da Música em 100% das conversas.
- [ ] G-02: 🟡 Consultar ferramentas antes de afirmar preço, estoque, prazo, desconto ou status de pedido.
- [ ] G-03: 🟡 Manter contexto de até 12 mensagens por sessão e persistir o histórico.
- [ ] G-04: 🟡 Encaminhar para humano quando houver reclamação, dúvida sem resposta ou pedido explícito.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Respostas de preço sem consulta em teste automatizado | 100% no protótipo inicial | 0 ocorrências | 2026-11-03 |
| Tempo de resposta final P95 | não medido | ≤ 8 s | 2026-11-03 |
| Cobertura de testes do loop | 0% | ≥ 70% | 2026-11-03 |
| Conversas com persona validada | não medido | 100% | 2026-11-03 |

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Não haverá fine-tuning nem treinamento de modelo próprio nesta versão.
- NG-02: 🟡 Não haverá voz, áudio ou atendimento telefônico; o canal é texto.
- NG-03: 🟡 Não haverá autonomia para criar pedido, cobrar pagamento ou alterar estoque.
- NG-04: 🟡 Não haverá atendimento multilíngue; a v1 responde em português do Brasil.

## 5. Usuários e Personas

**Usuário primário:** 🟡 Cliente da loja que envia mensagem pelo chat, representado por Marina na pré-venda e Rafael no pós-venda.

**Usuário secundário:** 🟡 Equipe de atendimento que recebe escalonamentos e consulta o histórico.

**Jornada atual (sem a feature):** 🟡 O cliente espera atendimento humano, repete dados e nem sempre recebe resposta fora do horário comercial.

**Jornada futura (com a feature):** 🟡 O cliente envia a mensagem, recebe resposta contextualizada em até 8 segundos e é encaminhado a humano quando necessário.

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve carregar a persona da Empório da Música em todas as respostas. | Must | Teste de prompt verifica tom informal, acolhedor e profissional em 100% das amostras. |
| RF-02 | O sistema deve registrar cada mensagem do usuário e do assistente no histórico da sessão. | Must | Consulta ao histórico retorna as mensagens na ordem cronológica. |
| RF-03 | O sistema deve manter as últimas 12 mensagens como contexto ativo da conversa. | Must | Teste com 20 mensagens confirma que apenas as 12 mais recentes entram no prompt. |
| RF-04 | O sistema deve executar ferramentas antes de afirmar preço, estoque, promoção, frete ou status de pedido. | Must | Resposta com valor em reais sem chamada de ferramenta é bloqueada pelo guardrail. |
| RF-05 | O sistema deve recusar perguntas fora do escopo com redirecionamento educado. | Must | Mensagem sobre acessórios recebe recusa e sugestão de loja parceira, sem preço inventado. |
| RF-06 | O sistema deve registrar escalonamento com motivo, resumo e data. | Must | Pedido de humano cria registro na tabela de handoffs com status aberto. |
| RF-07 | O sistema deve usar fallback de provedor quando o LLM principal falhar. | Should | Teste simula erro 503 no DeepSeek e confirma resposta pelo provedor secundário. |
| RF-08 | O sistema deve limitar o loop a 5 iterações de ferramentas por mensagem. | Must | Teste com ferramenta que sempre falha encerra em 5 iterações com mensagem de fallback. |
| RF-09 | O sistema deve mascarar telefone e e-mail em logs e respostas de depuração. | Must | Log de teste não contém o telefone completo do cliente. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário envia uma pergunta sobre preço de um produto.
2. 🟡 O sistema carrega persona, histórico e ferramentas disponíveis.
3. 🟡 O sistema identifica a necessidade e chama a ferramenta de catálogo.
4. 🟡 O sistema recebe o preço, a promoção e o estoque atuais.
5. 🟡 O sistema responde com o valor, a condição de pagamento e a disponibilidade.
6. 🟡 Resultado: a mensagem e a resposta ficam gravadas no histórico da sessão.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Pergunta fora do escopo:**
1. 🟡 O usuário pergunta sobre cordas de violão.
2. 🟡 O sistema informa que a loja trabalha apenas com instrumentos e sugere procurar uma loja parceira.
3. 🟡 O sistema não consulta preço de acessório e não inventa disponibilidade.

**Fluxo Alternativo B — Falha do provedor:**
1. 🟡 O provedor principal retorna erro 503 ou timeout.
2. 🟡 O sistema tenta o provedor secundário após 1 retry com espera de 1 segundo.
3. 🟡 O sistema responde com aviso de instabilidade e registra o incidente.

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Tempo de resposta final | ≤ 8 s para P95 | Inclui chamadas de ferramentas e LLM. |
| RNF-02 | Disponibilidade do chat | ≥ 99% em horário de teste | Protótipo local. |
| RNF-03 | Segurança | Nenhum dado de outro cliente em resposta | Validação de vínculo antes de consultar pedido. |
| RNF-04 | Acessibilidade | Navegação por teclado e contraste mínimo | UI simples com foco visível. |
| RNF-05 | Observabilidade | 100% das chamadas de ferramenta registradas | Log estruturado sem PII completa. |

## 8. Design e Interface

**Componentes afetados:** 🟡 Loop do agente, registro de ferramentas, prompts, guardrails, persistência de mensagens e adapters de LLM.

**Comportamento esperado:** 🟡 O usuário envia texto e vê indicador de digitação; a resposta aparece com formatação de preço em reais e citação de política quando aplicável.

**Estados da UI:**
- Estado vazio: 🟡 mensagem de boas-vindas com exemplos de perguntas.
- Estado de carregamento: 🟡 indicador de digitação e bloqueio de envio duplicado.
- Estado de erro: 🟡 mensagem de instabilidade com opção de tentar novamente.
- Estado de sucesso: 🟡 resposta exibida e histórico atualizado.

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
conversations {
  id: uuid          // identificador da conversa
  session_id: text  // identificador da sessão do navegador
  customer_id: int  // cliente identificado, quando houver
  created_at: timestamp
  updated_at: timestamp
}

messages {
  id: bigint        // identificador da mensagem
  conversation_id: uuid
  role: text        // user, assistant, tool ou system
  content: text
  tool_calls: jsonb
  citations: jsonb
  created_at: timestamp
}

handoffs {
  id: uuid
  conversation_id: uuid
  reason: text
  summary: text
  status: text      // aberto, em_atendimento, resolvido
  created_at: timestamp
}
```

**Migrações necessárias:** 🟡 Sim; criar as três tabelas no Supabase com índices por conversa e data.

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| DeepSeek API | Obrigatória | Fallback para OpenAI gpt-4o-mini; se ambos falharem, mensagem de indisponibilidade. |
| OpenAI API | Opcional | Usada apenas como fallback. |
| Gemini API | Opcional | Alternativa gratuita para desenvolvimento. |
| Supabase Postgres | Obrigatória | Histórico não persiste; modo local em memória para testes. |
| Catálogo, pedidos e políticas | Obrigatória | Sem consulta, o agente não afirma dados e oferece escalonamento. |

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: Timeout do LLM | Provedor não responde em 30 s | Tentar 1 retry e acionar fallback; se persistir, responder com aviso e registrar incidente. |
| EC-02: Tool call malformada | Modelo envia argumento inválido | Validar com Pydantic, devolver erro ao modelo e tentar novamente uma vez. |
| EC-03: Limite de iterações | Modelo chama ferramentas 5 vezes | Encerrar o loop e oferecer escalonamento humano. |
| EC-04: Pergunta fora do escopo | Assunto não relacionado à loja | Recusar com educação e redirecionar sem inventar dados. |
| EC-05: Pedido de dado de outro cliente | Usuário tenta consultar pedido alheio | Negar, explicar a necessidade de identificação e não revelar dados. |
| EC-06: Rate limit do provedor | Erro 429 | Aplicar backoff de 1 s, 2 s e 4 s; depois acionar fallback. |
| EC-07: Mensagem vazia ou muito longa | Texto vazio ou acima de 2.000 caracteres | Rejeitar com mensagem clara e limite de tamanho. |

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Não há login na v1; a sessão é identificada por UUID no navegador.
- **Autorização:** 🟡 Consultas de pedido exigem identificação do cliente e vínculo com o pedido.
- **Dados sensíveis:** 🟡 Telefone e e-mail são mascarados em logs; o histórico armazena apenas o necessário.
- **Auditoria:** 🟡 Registrar tool calls, citações, custo por conversa e escalonamentos.

## 13. Plano de Rollout

- **Estratégia:** 🟡 Big bang no ambiente local do desafio, com feature flag para fallback local.
- **Como reverter (rollback):** 🟡 Desativar a variável de ambiente do provedor e voltar ao modo em memória; restaurar o commit anterior.
- **Monitoramento pós-deploy:** 🟡 Observar erros de tool call, latência P95, taxa de escalonamento e respostas bloqueadas por guardrail nas primeiras 24 horas.

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | Qual é o SLA formal de retorno humano após escalonamento? | Médio | adelino | 2026-11-03 |
| OQ-02 | O limite de 12 mensagens de contexto é suficiente para conversas longas? | Baixo | adelino | 2026-11-03 |

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| Usar function calling com serviços determinísticos | Agente SQL livre, ReAct sem ferramentas | Reduz alucinação e mantém preço e estoque auditáveis. |
| DeepSeek como padrão | OpenAI, Gemini | Melhor custo-benefício e suporte a tool calls. |
| Fallback OpenAI gpt-4o-mini | Apenas DeepSeek | Aumenta disponibilidade e previsibilidade de schema. |
| Limite de 5 iterações | Loop aberto | Evita custo e latência sem controle. |

## Apêndice

### Referências
- PRD em _reversa_sdd/prd.md
- Manual de Políticas da Empório da Música
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
