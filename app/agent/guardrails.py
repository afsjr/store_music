from __future__ import annotations

import re

from app.domain.models import ToolResult
from app.domain.store_info import STORE_INFO
from app.domain.text import digits_only, normalize_text
from app.logging import mask_pii

EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]")
ALLOWED_PHONES = {digits_only(STORE_INFO.phone), digits_only(STORE_INFO.whatsapp)}
ALLOWED_EMAILS = {STORE_INFO.email.lower()}


def strip_formatting(text: str) -> str:
    text = EMOJI_RE.sub("", text or "")
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"[ \t]+\n", "\n", text).strip()


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
    """Mascara PII, remove formatação e bloqueia afirmações sem consulta às ferramentas."""
    cleaned = strip_formatting(text or "")
    masked = mask_pii(cleaned, allow_phones=ALLOWED_PHONES, allow_emails=ALLOWED_EMAILS)
    if contains_sensitive_claim(masked) and not tool_calls and not has_tool_history:
        return safe_fallback_response(), True
    return masked, False
