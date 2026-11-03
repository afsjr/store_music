from __future__ import annotations

import argparse
from pathlib import Path

from app.adapters.rag.pdf_loader import load_policy_chunks, sections_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida e resume o índice de políticas.")
    parser.add_argument("--pdf", default="emporio_musica/data/políticas_da_loja.pdf")
    parser.add_argument("--cache", default="data/policy_chunks.json")
    parser.add_argument("--output", default="docs/policy_index_summary.md")
    args = parser.parse_args()

    chunks = load_policy_chunks(Path(args.pdf), cache_path=Path(args.cache))
    summary = sections_summary(chunks)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Resumo do Índice de Políticas",
        "",
        f"**PDF:** `{args.pdf}`",
        f"**Chunks:** {len(chunks)}",
        f"**Seções:** {len(summary)}",
        "",
        "| Seção | Título | Página | Chunks | Caracteres |",
        "|---|---|---:|---:|---:|",
    ]
    for section, data in sorted(summary.items(), key=lambda item: item[0]):
        lines.append(
            f"| {section} | {data['title']} | {data['page']} | {data['chunks']} | {data['chars']} |"
        )
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")

    print(f"Chunks indexados: {len(chunks)}")
    print(f"Seções: {len(summary)}")
    print(f"Resumo: {output.resolve()}")


if __name__ == "__main__":
    main()
