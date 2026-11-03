# Benchmark de Latência — DeepSeek vs OpenAI

**Data:** 2026-11-03
**Execuções por cenário:** 3
**Cenários:** catálogo (1 ferramenta), pedido (2 ferramentas) e devolução (2 ferramentas + política).
**Modo:** Supabase, `STORE_TODAY=2026-02-20`, DeepSeek sem thinking, `max_tokens=800`.

## Resultados por cenário

| Provedor | Cenário | Mediana (s) | Média (s) | Mínimo (s) | Máximo (s) | Sucesso |
|---|---|---:|---:|---:|---:|---:|
| deepseek | catalogo | 10.709 | 11.306 | 10.66 | 12.548 | 3/3 |
| deepseek | pedido | 10.207 | 10.275 | 10.186 | 10.431 | 3/3 |
| deepseek | devolucao | 12.757 | 13.826 | 12.278 | 16.444 | 3/3 |
| openai | catalogo | 12.808 | 12.529 | 11.215 | 13.563 | 3/3 |
| openai | pedido | 11.679 | 11.628 | 10.817 | 12.388 | 3/3 |
| openai | devolucao | 11.65 | 12.723 | 10.76 | 15.759 | 3/3 |

## Consolidado

| Provedor | Mediana (s) | Média (s) | Sucesso |
|---|---:|---:|---:|
| deepseek | 10.709 | 11.802 | 9/9 |
| openai | 11.679 | 12.293 | 9/9 |

## Conclusão

O provedor com menor mediana de latência foi **deepseek** (10.709 s), com 9/9 execuções bem-sucedidas. O outro provedor deve ficar como fallback.
