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

OUT_OF_SCOPE_PATTERNS = (
    re.compile(
        r"\b(concorrente|outra loja|outras lojas|mercado livre|amazon|magazine luiza|"
        r"casas bahia|guitar center|sweetwater|aliexpress|shopee)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(advogado|advogada|processo judicial|juridico|justica|tribunal|"
        r"medico|medica|remedio|doenca|diagnostico|receita medica)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(politica partidaria|presidente|eleicao|deputado|senador|governo|"
        r"lula|bolsonaro|stf|congresso)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(futebol|flamengo|corinthians|palmeiras|cruzeiro|atletico|"
        r"campeonato|jogo do brasil)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(noticia|noticias|clima|previsao do tempo|receita de bolo|"
        r"capital da franca|capital do brasil|capital de portugal|"
        r"programacao|codigo python)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(geladeira|fogao|microondas|celular|computador|notebook|"
        r"televisao|carro|moto|roupa|sapato|comida)\b",
        re.IGNORECASE,
    ),
)


POLICY_TERMS = re.compile(
    r"\b("
    r"devolv|arrepend|troca|garantia|frete|entrega|parcel|pix|horario|endereco|"
    r"pagamento|politica|defeito|conserto|assistencia|prazo|cartao|credito|debito|"
    r"boleto|desconto|promoc|parcela|juros|abert|fechad|fundad|historia|lgpd|"
    r"dados|exclu|consentimento|correios|transportadora|motoboy|cep|peso|dimens|"
    r"preferencia|regulagem|boquilha|avaria|seguro|atendimento|expediente|sla"
    r")\w*"
    r"|\brain\s*check\b"
    r"|\bvenda\s+final\b"
    r"|\btempo\s+de\s+resposta\b"
    r"|\bfora\s+do\s+expediente\b"
    r"|\bsetup\b"
    r"|\bsedex\b"
    r"|\bjadlog\b"
    r"|\bpac\b",
    re.IGNORECASE,
)


def needs_policy_retrieval(message: str) -> bool:
    return bool(POLICY_TERMS.search(normalize_text(message)))


def is_accessory_request(message: str) -> bool:
    normalized = normalize_text(message)
    if not any(term in normalized for term in ACCESSORY_TERMS):
        return False
    # "violão com cordas de nylon" é pergunta sobre o instrumento, não sobre acessório.
    if "corda" in normalized and re.search(
        r"\b(com cordas|cordas de nylon|cordas de aco|cordas de aço)\b", normalized
    ):
        return False
    # "violão de 7 cordas" e modelos com "N cordas" no nome são instrumentos.
    if re.search(r"\b\d+\s*cordas\b", normalized):
        has_instrument = any(term in normalized for term in INSTRUMENT_TERMS)
        has_accessory_intent = bool(
            re.search(r"\b(reposicao|jogo|comprar|trocar|substituir)\b", normalized)
        )
        if has_instrument or not has_accessory_intent:
            return False
    return True


def is_out_of_scope_topic(message: str) -> bool:
    normalized = normalize_text(message)
    return any(pattern.search(normalized) for pattern in OUT_OF_SCOPE_PATTERNS)


def out_of_scope_response() -> str:
    return (
        "A Empório da Música trabalha apenas com instrumentos musicais e não comercializa "
        "acessórios como cordas, palhetas, cabos, cases, pedais ou amplificadores. "
        "Posso ajudar a encontrar um instrumento ou encaminhar seu contato para a equipe, "
        "que pode orientar sobre onde encontrar o acessório."
    )


def general_out_of_scope_response() -> str:
    return (
        "Posso ajudar apenas com instrumentos musicais, pedidos e políticas da Empório da "
        "Música. Para esse assunto, não consigo responder. Se quiser, posso encaminhar seu "
        "atendimento para a equipe."
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
