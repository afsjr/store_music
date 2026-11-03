# Brief inicial, /reversa-new

> Selo 🟡 PLANEJADO. Documento de entrada do time Code New Project Agents.

**Data:** 2026-11-03T14:14:25Z
**Usuário:** adelino

## Ideia original

Construir um agente de atendimento por mensagens de texto para a Empório da Música, loja fictícia de instrumentos musicais em Campo Grande/MS, para reduzir a carga da equipe em perguntas recorrentes. O agente deve assumir a persona definida no manual de políticas (informal, acolhedora e profissional), responder com base no catálogo, estoque, preços, promoções, pedidos e políticas da loja, e saber quando consultar dados estruturados e quando consultar o manual de políticas.

O projeto será em Python, com FastAPI e uma UI simples de chat. Os CSVs serão carregados em um projeto Supabase e as consultas serão feitas por repositórios com interfaces bem definidas, mantendo alta coesão e baixo acoplamento. O agente usará function calling com ferramentas determinísticas para catálogo, pedidos, promoções, frete e escalonamento, além de RAG sobre o manual de políticas; a estratégia de RAG será decidida após a geração das specs do Reversa (BM25/TF-IDF por seção é a recomendação inicial). O LLM padrão será DeepSeek Flash, com adapter para OpenAI gpt-4o-mini como fallback e Gemini como alternativa gratuita.

O escopo da v1 é consulta e escalonamento humano. Criação de carrinho/pedido fica como backlog. O agente deve lidar com perguntas fora do escopo (acessórios, concorrentes, assuntos não relacionados), proteger dados de clientes, não inventar preços/estoque/prazos e aplicar corretamente as políticas de troca, devolução, garantia, pagamento, frete e horário.

Entregáveis: repositório público com commits incrementais em português, README com decisões e limitações, 3 a 5 exemplos de conversa e testes automatizados. A data de referência para prazos será configurável (`STORE_TODAY`), com padrão na data real.

---
Gerado por /reversa-new em 2026-11-03T14:14:25Z
