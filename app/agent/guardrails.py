from __future__ import annotations

import re
import unicodedata

from app.domain.models import ToolResult
from app.logging import mask_pii


def normalize_text(value: str) -> str:
    text = (value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


ACCESSORY_TERMS = (
    "corda",
    "cordas",
    "palheta",
    "palhetas",
    "cabo",
    "cabos",
    "case",
    "cases",
    "pedal",
    "pedais",
    "amplificador",
    "amplificadores",
    "acessorio",
    "acessorios",
)

INSTRUMENT_TERMS = (
    "violao",
    "violoes",
    "guitarra",
    "guitarras",
    "baixo",
    "baixos",
    "ukulele",
    "ukuleles",
    "bateria",
    "teclado",
    "piano",
    "saxofone",
    "flauta",
    "violino",
    "instrumento",
)

SENSITIVE_PATTERNS = (
    re.compile(r"R\$\s*\d", re.IGNORECASE),
    re.compile(r"\b(em estoque|dispon[ií]vel|esgotado|sem estoque)\b", re.IGNORECASE),
    re.compile(r"\b(rastreio|rastreamento)\b", re.IGNORECASE),
    re.compile(r"\b(pedido|order)\s*#?\s*\d+", re.IGNORECASE),
    re.compile(r"\b(status|entregue|enviado|confirmado|pendente|cancelado)\b", re.IGNORECASE),
)


def is_accessory_request(message: str) -> bool:
    normalized = normalize_text(message)
    if not any(term in normalized for term in ACCESSORY_TERMS):
        return False
    # "violão com cordas de nylon" é pergunta sobre o instrumento, não sobre acessório.
    if "corda" in normalized and re.search(
        r"\b(com cordas|cordas de nylon|cordas de aco|cordas de aço)\b", normalized
    ):
        return False
    return True


def out_of_scope_response() -> str:
    return (
        "A Empório da Música trabalha apenas com instrumentos musicais e não comercializa "
        "acessórios como cordas, palhetas, cabos, cases, pedais ou amplificadores. "
        "Posso te ajudar a encontrar um instrumento ou indicar uma loja parceira para o acessório."
    )


def safe_fallback_response() -> str:
    return (
        "Não consegui confirmar essa informação com segurança agora. "
        "Posso encaminhar seu atendimento para a equipe, que responde em até 24 horas úteis."
    )


def contains_sensitive_claim(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in SENSITIVE_PATTERNS)


def sanitize_response(
    text: str,
    tool_calls: list[ToolResult],
    has_tool_history: bool = False,
) -> tuple[str, bool]:
    """Mascara PII e bloqueia afirmações de dados sem consulta às ferramentas."""
    masked = mask_pii(text or "")
    if contains_sensitive_claim(masked) and not tool_calls and not has_tool_history:
        return safe_fallback_response(), True
    return masked, False
