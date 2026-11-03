from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.adapters.llm.openai_compatible import OpenAICompatibleClient
from app.config import Settings, get_settings
from app.main import create_app

SCENARIOS = [
    {
        "id": "catalogo",
        "message": "Quais violões custam até R$ 1000?",
        "expected_tools": ["buscar_produtos"],
        "expected_text": "R$",
    },
    {
        "id": "pedido",
        "message": (
            "Meu pedido 8 chegou? Meu nome é Ana Carolina Ferreira e meu telefone "
            "é (67) 99654-7821."
        ),
        "expected_tools": ["identificar_cliente", "consultar_pedido"],
        "expected_text": "BRJL5544332BR",
    },
    {
        "id": "devolucao",
        "message": (
            "Meu nome é Letícia Gonçalves Rocha, telefone (67) 99789-0123. "
            "Me arrependi da compra do pedido 7. Posso devolver?"
        ),
        "expected_tools": ["identificar_cliente", "consultar_pedido"],
        "expected_text": "7 dias",
    },
]


def _client(provider: str, settings: Settings) -> OpenAICompatibleClient:
    if provider == "deepseek":
        return OpenAICompatibleClient(
            api_key=settings.deepseek_api_key or "",
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout=settings.llm_timeout_seconds,
            max_tokens=settings.llm_max_tokens,
            extra_body={"thinking": {"type": "disabled"}},
        )
    return OpenAICompatibleClient(
        api_key=settings.openai_api_key or "",
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        timeout=settings.llm_timeout_seconds,
        max_tokens=settings.llm_max_tokens,
    )


def _run_provider(provider: str, runs: int, settings: Settings) -> list[dict]:
    client = _client(provider, settings)
    app = create_app(settings=settings, llm=client)
    http = TestClient(app)

    # Aquecimento: inicializa pool, store, índice e caches.
    session = http.post("/api/sessions").json()["session_id"]
    http.post(
        "/api/chat",
        json={"session_id": session, "message": SCENARIOS[0]["message"]},
    )

    results: list[dict] = []
    for scenario in SCENARIOS:
        for run in range(1, runs + 1):
            session = http.post("/api/sessions").json()["session_id"]
            started = time.perf_counter()
            response = http.post(
                "/api/chat",
                json={"session_id": session, "message": scenario["message"]},
            )
            elapsed = time.perf_counter() - started
            data = response.json()
            tools = [item["name"] for item in data.get("tool_calls", [])]
            success = (
                response.status_code == 200
                and all(tool in tools for tool in scenario["expected_tools"])
                and scenario["expected_text"] in (data.get("reply") or "")
            )
            results.append(
                {
                    "provider": provider,
                    "scenario": scenario["id"],
                    "run": run,
                    "latency_s": round(elapsed, 3),
                    "status": response.status_code,
                    "success": success,
                    "tools": tools,
                    "handoff": data.get("handoff", False),
                    "reply_len": len(data.get("reply") or ""),
                }
            )
            print(
                f"{provider:8} {scenario['id']:10} run={run} "
                f"{elapsed:6.2f}s status={response.status_code} "
                f"success={success} tools={tools}"
            )
    return results


def _stats(values: list[float]) -> dict:
    if not values:
        return {"median": None, "mean": None, "min": None, "max": None}
    return {
        "median": round(statistics.median(values), 3),
        "mean": round(statistics.mean(values), 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
    }


def _write_report(results: list[dict], runs: int, path: Path) -> None:
    providers = sorted({item["provider"] for item in results})
    lines = [
        "# Benchmark de Latência — DeepSeek vs OpenAI",
        "",
        "**Data:** 2026-11-03",
        f"**Execuções por cenário:** {runs}",
        "**Cenários:** catálogo (1 ferramenta), pedido (2 ferramentas) e devolução (2 ferramentas + política).",
        "**Modo:** Supabase, `STORE_TODAY=2026-02-20`, DeepSeek sem thinking, `max_tokens=800`.",
        "",
        "## Resultados por cenário",
        "",
        "| Provedor | Cenário | Mediana (s) | Média (s) | Mínimo (s) | Máximo (s) | Sucesso |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for provider in providers:
        for scenario in SCENARIOS:
            subset = [
                item
                for item in results
                if item["provider"] == provider and item["scenario"] == scenario["id"]
            ]
            stats = _stats([item["latency_s"] for item in subset])
            success = sum(1 for item in subset if item["success"])
            lines.append(
                f"| {provider} | {scenario['id']} | {stats['median']} | {stats['mean']} | "
                f"{stats['min']} | {stats['max']} | {success}/{len(subset)} |"
            )

    lines.extend(
        [
            "",
            "## Consolidado",
            "",
            "| Provedor | Mediana (s) | Média (s) | Sucesso |",
            "|---|---:|---:|---:|",
        ]
    )
    summary: dict[str, dict] = {}
    for provider in providers:
        subset = [item for item in results if item["provider"] == provider]
        stats = _stats([item["latency_s"] for item in subset])
        success = sum(1 for item in subset if item["success"])
        summary[provider] = {
            **stats,
            "success": success,
            "total": len(subset),
        }
        lines.append(
            f"| {provider} | {stats['median']} | {stats['mean']} | {success}/{len(subset)} |"
        )

    ordered = [(provider, data) for provider, data in summary.items() if data["median"] is not None]
    ordered.sort(key=lambda item: item[1]["median"] or 9999)
    lines.extend(["", "## Conclusão", ""])
    if ordered:
        winner, winner_data = ordered[0]
        lines.append(
            f"O provedor com menor mediana de latência foi **{winner}** "
            f"({winner_data['median']} s), com {winner_data['success']}/{winner_data['total']} "
            "execuções bem-sucedidas. O outro provedor deve ficar como fallback."
        )
    else:
        lines.append("Não houve execuções suficientes para concluir.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("docs/llm_benchmark.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("\nResumo:")
    for provider, data in summary.items():
        print(
            f"  {provider}: mediana={data['median']}s media={data['mean']}s "
            f"sucesso={data['success']}/{data['total']}"
        )
    print(f"\nRelatório: {path.resolve()}")
    print("JSON: docs/llm_benchmark.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara latência de DeepSeek e OpenAI.")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output", default="docs/llm_benchmark.md")
    args = parser.parse_args()

    base = get_settings()
    if not base.deepseek_api_key or not base.openai_api_key:
        print("Configure DEEPSEEK_API_KEY e OPENAI_API_KEY no .env para rodar o benchmark.")
        raise SystemExit(1)

    settings = Settings(
        _env_file=None,
        local_mode=False,
        supabase_db_url=base.supabase_db_url,
        data_dir=base.data_dir,
        policy_pdf=base.policy_pdf,
        policy_cache=base.policy_cache,
        llm_provider="deepseek",
        deepseek_model=base.deepseek_model,
        openai_model=base.openai_model,
        deepseek_api_key=base.deepseek_api_key,
        deepseek_base_url=base.deepseek_base_url,
        openai_api_key=base.openai_api_key,
        openai_base_url=base.openai_base_url,
        llm_timeout_seconds=base.llm_timeout_seconds,
        llm_max_tokens=base.llm_max_tokens,
        llm_thinking=False,
        store_today="2026-02-20",
    )

    results: list[dict] = []
    results.extend(_run_provider("deepseek", args.runs, settings))
    results.extend(_run_provider("openai", args.runs, settings))
    _write_report(results, args.runs, Path(args.output))


if __name__ == "__main__":
    main()
