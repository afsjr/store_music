from __future__ import annotations

import unicodedata

from app.domain.models import ShippingQuote
from app.domain.store_info import (
    CAMPO_GRANDE_METRO,
    LOCAL_FLAT_FEE,
    LOCAL_FREE_THRESHOLD,
)


def normalize_city(value: str) -> str:
    text = (value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


class ShippingService:
    def quote(self, city: str, subtotal: float, cep: str | None = None) -> ShippingQuote:
        normalized = normalize_city(city)
        if not normalized:
            return ShippingQuote(
                city=city or "não informada",
                subtotal=subtotal,
                kind="cotacao",
                message="Informe a cidade e o CEP para calcular o frete.",
            )
        if normalized not in CAMPO_GRANDE_METRO:
            return ShippingQuote(
                city=city,
                subtotal=subtotal,
                kind="cotacao",
                message=(
                    "Para cidades fora da região metropolitana de Campo Grande, o frete é "
                    "calculado por CEP, peso e dimensões. Informe o CEP para cotação."
                ),
            )
        if subtotal >= LOCAL_FREE_THRESHOLD:
            return ShippingQuote(
                city=city,
                subtotal=subtotal,
                kind="gratis",
                amount_brl=0.0,
                message="Frete grátis para pedidos a partir de R$ 500,00 na região metropolitana.",
            )
        return ShippingQuote(
            city=city,
            subtotal=subtotal,
            kind="fixo",
            amount_brl=LOCAL_FLAT_FEE,
            message="Taxa fixa de R$ 35,00 para pedidos abaixo de R$ 500,00.",
        )
