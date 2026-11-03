# Spec: API e UI

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-11-03
**Reviewers:** N/A

---

## 1. Resumo

🟡 A feature entrega a API FastAPI e uma interface web simples de chat para o agente. Ela existe para permitir que o cliente envie mensagens, veja respostas e retome o histórico, com endpoints claros para integração e testes.

## 2. Contexto e Motivação

**Problema:** 🟡 O agente precisa de um canal de interação demonstrável. Uma UI simples e uma API documentada permitem validar o atendimento, capturar exemplos e integrar o agente a outros canais no futuro.

**Evidências:** 🟡 O desafio aceita CLI, notebook, API ou UI simples. A escolha aprovada foi FastAPI com UI vanilla, mantendo baixo acoplamento e foco no agente.

**Por que agora:** 🟡 O prazo de entrega é 03/11/2026 até 19h; a interface precisa ficar pronta junto com o núcleo do agente.

## 3. Goals (Objetivos)

- [ ] G-01: 🟡 Disponibilizar endpoint de chat com sessão e resposta do agente.
- [ ] G-02: 🟡 Servir uma UI de chat com histórico e nova conversa.
- [ ] G-03: 🟡 Expor health check com estado do banco e do provedor de LLM.
- [ ] G-04: 🟡 Retornar erros claros sem expor stack trace ou segredo.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Latência P95 do endpoint de chat | não medido | ≤ 8 s | 2026-11-03 |
| Health check | não medido | ≤ 1 s | 2026-11-03 |
| Cobertura de testes dos endpoints | 0% | ≥ 70% | 2026-11-03 |
| Exemplos de conversa capturados pela UI | 0 | 3 a 5 | 2026-11-03 |

## 4. Non-Goals (Fora do Escopo)

- NG-01: 🟡 Não haverá login, cadastro ou autenticação de usuário nesta versão.
- NG-02: 🟡 Não haverá integração real com WhatsApp, SMS ou e-mail.
- NG-03: 🟡 Não haverá upload de arquivos, imagem ou áudio.
- NG-04: 🟡 Não haverá painel administrativo ou edição de catálogo pela UI.
- NG-05: 🟡 Não haverá streaming token a token na v1; a resposta será retornada completa.

## 5. Usuários e Personas

**Usuário primário:** 🟡 Cliente da loja que usa o chat no navegador, representado por Marina e Rafael.

**Usuário secundário:** 🟡 Avaliador técnico que executa a API, lê os exemplos e testa os endpoints.

**Jornada atual (sem a feature):** 🟡 O agente só pode ser testado por script ou terminal, o que dificulta a demonstração.

**Jornada futura (com a feature):** 🟡 O cliente abre a página, envia a mensagem, recebe a resposta e pode iniciar uma nova conversa ou continuar a anterior.

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve expor POST /api/chat com session_id e message. | Must | Requisição válida retorna reply, citations e handoff. |
| RF-02 | O sistema deve criar sessão quando o cliente não enviar session_id. | Must | POST /api/sessions retorna UUID de sessão. |
| RF-03 | O sistema deve retornar o histórico da sessão em GET /api/sessions/{id}/messages. | Must | Histórico retorna mensagens na ordem cronológica. |
| RF-04 | O sistema deve servir a UI de chat em GET /. | Must | Navegador recebe HTML, CSS e JavaScript da UI. |
| RF-05 | O sistema deve exibir indicador de digitação enquanto aguarda a resposta. | Must | UI mostra indicador após o envio e remove ao receber a resposta. |
| RF-06 | O sistema deve permitir iniciar nova conversa e limpar a sessão atual. | Must | Botão nova conversa gera novo session_id e limpa a tela. |
| RF-07 | O sistema deve expor GET /health com estado do banco e do LLM. | Must | Health retorna 200 quando banco e LLM estão configurados. |
| RF-08 | O sistema deve limitar a mensagem a 2.000 caracteres. | Must | Mensagem acima do limite retorna erro 422 com mensagem clara. |
| RF-09 | O sistema deve retornar erro 503 quando o agente estiver indisponível. | Must | Falha do LLM retorna 503 e mensagem amigável. |
| RF-10 | O sistema deve registrar request_id e latência por requisição. | Should | Log contém request_id e duração em milissegundos. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O cliente abre a página inicial no navegador.
2. 🟡 A UI cria ou recupera o session_id no localStorage.
3. 🟡 O cliente digita uma pergunta e envia.
4. 🟡 A UI chama POST /api/chat e mostra o indicador de digitação.
5. 🟡 O backend aciona o agente e recebe a resposta.
6. 🟡 A UI exibe a resposta e atualiza o histórico.
7. 🟡 Resultado: a conversa fica visível e pode continuar na mesma sessão.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Sessão não encontrada:**
1. 🟡 A UI envia um session_id inexistente.
2. 🟡 O backend cria uma nova sessão e retorna o novo identificador.
3. 🟡 A UI atualiza o localStorage sem perder a mensagem enviada.

**Fluxo Alternativo B — LLM indisponível:**
1. 🟡 O agente retorna erro de indisponibilidade.
2. 🟡 A API responde 503 com mensagem amigável.
3. 🟡 A UI mostra aviso e permite tentar novamente.

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Latência do chat | ≤ 8 s para P95 | Inclui LLM e ferramentas. |
| RNF-02 | Health check | ≤ 1 s | Verificação leve de configuração. |
| RNF-03 | Segurança | CORS restrito à mesma origem | UI servida pelo próprio FastAPI. |
| RNF-04 | Acessibilidade | Navegação por teclado e rótulos ARIA | Campo de mensagem e botão de envio. |
| RNF-05 | Observabilidade | 100% das requisições com request_id | Log estruturado em JSON. |

## 8. Design e Interface

**Componentes afetados:** 🟡 Rotas FastAPI, schemas Pydantic, tratamento de erros, arquivos estáticos, JavaScript do chat e armazenamento de sessão.

**Comportamento esperado:** 🟡 A tela tem cabeçalho da Empório da Música, área de mensagens, campo de texto e botão de envio. A resposta aparece como balão do assistente com citações quando existirem.

**Estados da UI:**
- Estado vazio: 🟡 mensagem de boas-vindas e sugestões de perguntas.
- Estado de carregamento: 🟡 indicador de digitação e botão de envio desabilitado.
- Estado de erro: 🟡 faixa de aviso com opção de tentar novamente.
- Estado de sucesso: 🟡 resposta exibida e histórico atualizado.

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
conversations {
  id: uuid
  session_id: text
  customer_id: int
  created_at: timestamp
  updated_at: timestamp
}

messages {
  id: bigint
  conversation_id: uuid
  role: text
  content: text
  tool_calls: jsonb
  citations: jsonb
  created_at: timestamp
}
```

**Migrações necessárias:** 🟡 Sim; reutilizar as tabelas da spec de conversa e adicionar índice em session_id.

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| FastAPI e Uvicorn | Obrigatória | Sem servidor, a UI e a API não sobem. |
| Agente de conversa | Obrigatória | Sem agente, o chat retorna 503. |
| Supabase Postgres | Obrigatória | Histórico não persiste; fallback em memória para testes. |
| Arquivos estáticos | Obrigatória | Sem HTML, CSS e JS, a UI não carrega. |
| Navegador moderno | Obrigatória | Cliente acessa a interface. |

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: Mensagem vazia | Texto em branco | Retornar 422 e pedir uma mensagem. |
| EC-02: Mensagem acima do limite | Mais de 2.000 caracteres | Retornar 422 com o limite permitido. |
| EC-03: Sessão inexistente | session_id não encontrado | Criar nova sessão e devolver o identificador. |
| EC-04: LLM indisponível | Timeout ou erro 503 do provedor | Retornar 503 com mensagem amigável e fallback. |
| EC-05: Banco indisponível | Falha de conexão | Usar memória e avisar que o histórico pode não persistir. |
| EC-06: Requisição duplicada | Duplo clique no envio | Desabilitar botão e ignorar envio concorrente. |
| EC-07: Rate limit | Muitas requisições por sessão | Retornar 429 e pedir espera de 60 s. |

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Não há login; a sessão é um UUID aleatório.
- **Autorização:** 🟡 A sessão só acessa as próprias mensagens.
- **Dados sensíveis:** 🟡 A UI não exibe telefone ou e-mail completos; logs usam request_id.
- **Auditoria:** 🟡 Registrar session_id, request_id, latência e status HTTP, sem conteúdo sensível.

## 13. Plano de Rollout

- **Estratégia:** 🟡 Big bang no ambiente local, com a UI servida pelo mesmo processo FastAPI.
- **Como reverter (rollback):** 🟡 Voltar ao commit anterior e usar a API diretamente para testes.
- **Monitoramento pós-deploy:** 🟡 Observar erros 5xx, latência P95, taxa de 429 e falhas de health check.

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | A v1 deve exibir o painel de debug de tool calls para o avaliador? | Médio | adelino | 2026-11-03 |
| OQ-02 | O session_id deve expirar após quanto tempo de inatividade? | Baixo | adelino | 2026-11-03 |

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| FastAPI com UI vanilla | Streamlit, notebook, CLI | Atende à escolha do usuário e mantém baixo acoplamento. |
| Sessão em localStorage | Login com usuário | Simples para protótipo e suficiente para histórico. |
| Resposta completa sem streaming | SSE token a token | Menor complexidade e suficiente para o desafio. |
| Health check leve | Verificação profunda do banco | Evita latência e falsos negativos. |

## Apêndice

### Referências
- PRD em _reversa_sdd/prd.md
- Specs de conversa, catálogo, pedidos, políticas e plataforma de dados
- FastAPI e Pydantic

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
