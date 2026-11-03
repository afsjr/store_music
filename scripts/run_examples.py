from __future__ import annotations

import textwrap
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

SCENARIOS = [
    (
        "01-catalogo",
        "Catálogo por faixa de preço",
        ["Quais violões custam até R$ 1000?"],
    ),
    (
        "02-preco-promocao",
        "Preço e promoção",
        ["Quanto custa o Takamine GD20? Tem alguma promoção ativa? Como fica no PIX e em 6x?"],
    ),
    (
        "03-pedido",
        "Consulta de pedido com identificação",
        ["Meu pedido 8 chegou? Meu nome é Ana Carolina Ferreira e meu telefone é (67) 99654-7821."],
    ),
    (
        "04-devolucao",
        "Aplicação da política de devolução",
        [
            "Meu nome é Letícia Gonçalves Rocha, telefone (67) 99789-0123. "
            "Me arrependi da compra do pedido 7. Posso devolver?"
        ],
    ),
    (
        "05-fora-de-escopo",
        "Pergunta fora do escopo",
        ["Vocês vendem cordas de violão?"],
    ),
]


def _write_example(path: Path, title: str, messages: list[tuple[str, str, list, bool]]) -> None:
    lines = [f"# {title}", "", "> Exemplo gerado pelo runner local com o agente real.", ""]
    for role, content, citations, handoff in messages:
        label = "Cliente" if role == "user" else "Agente"
        lines.append(f"**{label}:** {content}")
        if citations:
            chips = ", ".join(
                f"Manual, seção {citation['section']}, p. {citation['page']}"
                for citation in citations
            )
            lines.append(f"*Fontes: {chips}*")
        if handoff:
            lines.append("*Atendimento encaminhado para a equipe.*")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    settings = Settings(store_today="2026-02-20")
    if not settings.llm_configured:
        print(
            "Nenhum provedor de LLM configurado. Preencha DEEPSEEK_API_KEY no .env "
            "para gerar exemplos reais."
        )
        raise SystemExit(1)

    app = create_app(settings=settings)
    client = TestClient(app)
    output_dir = Path("examples")
    output_dir.mkdir(exist_ok=True)

    for slug, title, user_messages in SCENARIOS:
        session = client.post("/api/sessions").json()
        session_id = session["session_id"]
        transcript: list[tuple[str, str, list, bool]] = []
        for message in user_messages:
            transcript.append(("user", message, [], False))
            response = client.post(
                "/api/chat",
                json={"session_id": session_id, "message": message},
            )
            if response.status_code != 200:
                print(f"Falha no cenário {slug}: {response.status_code} {response.text}")
                break
            data = response.json()
            transcript.append(
                (
                    "assistant",
                    data["reply"],
                    data.get("citations", []),
                    bool(data.get("handoff")),
                )
            )
        else:
            _write_example(output_dir / f"{slug}.md", title, transcript)
            print(f"Exemplo gerado: {output_dir / f'{slug}.md'}")

    print(
        textwrap.dedent(
            """
            Exemplos concluídos. Revise os arquivos em examples/ antes de commitar.
            """
        ).strip()
    )


if __name__ == "__main__":
    main()
