from __future__ import annotations

from datetime import date


def format_brl(value: float | None) -> str:
    if value is None:
        return "valor não informado"
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_date(value: date | None) -> str:
    if value is None:
        return "data não informada"
    return value.strftime("%d/%m/%Y")
