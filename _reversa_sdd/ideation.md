# Ideation, Empório da Música

> Selo 🟡 PLANEJADO em todos os itens, sujeito a validação.

## Brief original

Construir um agente de atendimento por mensagens de texto para a Empório da Música, loja fictícia de instrumentos musicais em Campo Grande/MS, para reduzir a carga da equipe em perguntas recorrentes. O agente deve assumir a persona definida no manual de políticas (informal, acolhedora e profissional), responder com base no catálogo, estoque, preços, promoções, pedidos e políticas da loja, e saber quando consultar dados estruturados e quando consultar o manual de políticas.

O projeto será em Python, com FastAPI e uma UI simples de chat. Os CSVs serão carregados em um projeto Supabase e as consultas serão feitas por repositórios com interfaces bem definidas, mantendo alta coesão e baixo acoplamento. O agente usará function calling com ferramentas determinísticas para catálogo, pedidos, promoções, frete e escalonamento, além de RAG sobre o manual de políticas; a estratégia de RAG será decidida após a geração das specs do Reversa (BM25/TF-IDF por seção é a recomendação inicial). O LLM padrão será DeepSeek Flash, com adapter para OpenAI gpt-4o-mini como fallback e Gemini como alternativa gratuita.

O escopo da v1 é consulta e escalonamento humano. Criação de carrinho/pedido fica como backlog. O agente deve lidar com perguntas fora do escopo (acessórios, concorrentes, assuntos não relacionados), proteger dados de clientes, não inventar preços/estoque/prazos e aplicar corretamente as políticas de troca, devolução, garantia, pagamento, frete e horário.

Entregáveis: repositório público com commits incrementais em português, README com decisões e limitações, 3 a 5 exemplos de conversa e testes automatizados. A data de referência para prazos será configurável (`STORE_TODAY`), com padrão na data real.

## Problema

🟡 A equipe de atendimento da Empório da Música está sobrecarregada com perguntas recorrentes sobre horários, status de pedido, preço e disponibilidade de produtos. O problema é sentido pela equipe, que perde tempo com casos simples, e pelos clientes, que enfrentam espera para obter informações básicas.

## Valor entregue

🟡 O cliente consegue resolver dúvidas de catálogo, pedido, promoções e políticas em segundos, a qualquer hora, enquanto a equipe foca em casos complexos, negociações e atendimento humano.

## Alternativas existentes

🟡 Atendimento 100% manual pela equipe; FAQ ou posts no Instagram; respostas prontas no WhatsApp; marketplaces e lojas concorrentes. Essas alternativas não bastam porque não consultam estoque, preço, pedido e políticas em tempo real, nem aplicam consistentemente as regras da loja.

## Público-alvo (bruto)

🟡 Clientes da Empório da Música, de iniciantes a profissionais, localizados em Campo Grande/MS e região, que compram instrumentos musicais e precisam de informações antes ou depois da compra.

## Métricas de sucesso

🟡
- Reduzir em 40% as perguntas repetitivas atendidas pela equipe em 3 meses.
- Primeira resposta em até 1 minuto durante o horário de funcionamento.
- Pelo menos 90% de respostas corretas em auditoria amostral.
- Taxa de escalonamento para humano abaixo de 20% das conversas.

## Premissas a validar

🟡
- Os dados de catálogo, estoque, preços e pedidos no Supabase estão corretos e atualizados.
- O LLM consegue seguir as regras de negócio e usar as ferramentas sem inventar preço, estoque ou prazo.
- As políticas da loja permanecem estáveis e a base de conhecimento é atualizada quando houver mudança.

## Notas

🟡 A v1 cobre consulta e escalonamento humano; criação de carrinho e pedido fica como backlog. O agente não vende acessórios, não compartilha dados de outros clientes e deve aplicar as políticas de troca, devolução, garantia, pagamento, frete e horário. A data de referência para prazos será configurável por `STORE_TODAY`, com padrão na data real. O manual de políticas é a fonte para o tom de voz e para as regras de atendimento.

---
Gerado por reversa-ideator em 2026-11-03T14:16:58Z
Fonte: newproject-brief.md
