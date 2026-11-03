# Onboarding: Agente de Atendimento Empório da Música — MVP

> Identificador: `001-atendimento-mvp`
> Data: `2026-11-03`
> Objetivo: permitir que uma pessoa execute e teste a feature pela primeira vez.

## 1. Pré-requisitos

- 🟡 Python 3.10 ou superior.
- 🟡 Git.
- 🟡 Conta e projeto Supabase com `SUPABASE_DB_URL` (opcional para o modo local).
- 🟡 Chave da API DeepSeek (opcional para testes com LLM falso).
- 🟡 Acesso ao diretório `emporio_musica/data/` com os CSVs e o PDF do manual.

## 2. Clonar e preparar o ambiente

```bash
git clone https://github.com/afsjr/store_music.git
cd store_music
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Preencha `.env`:

```dotenv
APP_ENV=local
DATA_DIR=emporio_musica/data
POLICY_PDF=emporio_musica/data/políticas_da_loja.pdf
LOCAL_MODE=true
STORE_TODAY=
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-flash
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
SUPABASE_DB_URL=
```

- 🟡 `LOCAL_MODE=true` usa os CSVs em memória e não exige Supabase.
- 🟡 `STORE_TODAY` vazio usa a data real; para reproduzir exemplos, informe `2026-02-20`.
- 🟡 Sem `DEEPSEEK_API_KEY`, os testes usam um LLM falso; a UI exibirá aviso de configuração.

## 4. Preparar o Supabase (opcional para o modo local)

```bash
psql "$SUPABASE_DB_URL" -f supabase/migrations/001_schema.sql
python scripts/ingest.py --dry-run
python scripts/ingest.py
```

O script deve exibir as contagens 9, 65, 50, 20, 22 e 25 e gerar `docs/data_quality_report.md`.

## 5. Construir o índice de políticas

```bash
python scripts/build_policy_index.py
```

O comando lê o PDF, divide por seções e grava o índice usado pelo RAG.

## 6. Subir a aplicação

```bash
uvicorn app.main:app --reload --port 8000
```

Abra `http://localhost:8000` no navegador.

## 7. Testar a API

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/sessions
curl -s -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"COLE-O-ID","message":"Quais violões custam até R$ 1000?"}'
```

## 8. Rodar testes e lint

```bash
pytest -q
ruff check .
ruff format --check .
```

## 9. Gerar exemplos de conversa

```bash
python scripts/run_examples.py
```

Os arquivos são gravados em `examples/` com os cenários de catálogo, pedido, política, fora de escopo e privacidade.

## 10. Problemas comuns

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| Health retorna 503 | Provedor de LLM não configurado | Preencha `DEEPSEEK_API_KEY` ou use o modo de teste. |
| Ingestão falha com FK | CSV inconsistente | Rode `--dry-run` e leia o relatório de qualidade. |
| Busca não retorna produto | Índice não construído ou banco vazio | Rode a ingestão e o build do índice. |
| Histórico não persiste | `SUPABASE_DB_URL` ausente | Use `LOCAL_MODE=true` ou configure o Supabase. |
| Resposta sem citação | Pergunta não é de política | Verifique se a ferramenta de políticas foi chamada. |

## 11. Critério de sucesso do onboarding

- 🟡 A aplicação sobe em menos de 5 minutos no modo local.
- 🟡 O health check retorna 200.
- 🟡 A UI responde a uma pergunta de catálogo.
- 🟡 Os testes passam sem credenciais externas.
- 🟡 Os exemplos são gerados em `examples/`.

## 12. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-03 | Versão inicial gerada por `/reversa-plan` | reversa |
