from __future__ import annotations

from app.domain.models import StoreInfo

STORE_INFO = StoreInfo(
    trade_name="Empório da Música",
    legal_name="Empório da Música Instrumentos Musicais Ltda.",
    cnpj="12.345.678/0001-90",
    address="Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, 79202-333",
    phone="(67) 3341-4444",
    whatsapp="(67) 3321-4500",
    email="contato@emporiodamusica.com.br",
    hours={
        "segunda_a_sexta": "09:00 às 18:00",
        "sabado": "09:00 às 13:00",
        "domingo_e_feriados": "Fechado",
    },
    source="Manual de Políticas e Procedimentos v2.1 — Junho/2025",
)

# Cidades tratadas como região metropolitana de Campo Grande no protótipo.
# A base de clientes não traz CEP; para as demais cidades, o frete é sob cotação.
CAMPO_GRANDE_METRO = {
    "campo grande",
    "terenos",
    "sidrolandia",
    "nova alvorada do sul",
    "ribas do rio pardo",
    "jaraguari",
    "bandeirantes",
    "rochedo",
    "corguinho",
    "dois irmaos do buriti",
}

LOCAL_FREE_THRESHOLD = 500.0
LOCAL_FLAT_FEE = 35.0
