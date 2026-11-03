from __future__ import annotations

from app.domain.format import format_brl
from app.domain.models import PaymentSimulation, Product
from app.domain.text import normalize_text

PIX_DISCOUNT_PERCENT = 5.0
MIN_INSTALLMENT_4X_6X = 80.0
MIN_INSTALLMENT_7X_12X = 100.0
MIN_PURCHASE_FOR_INSTALLMENTS = 50.0
COMBINATION_THRESHOLD = 2000.0

PAYMENT_ALIASES = {
    "pix": "pix",
    "debito": "debito",
    "debit": "debito",
    "cartao de debito": "debito",
    "credito": "credito",
    "credit": "credito",
    "cartao de credito": "credito",
    "cartao": "credito",
    "boleto": "boleto",
    "boleto bancario": "boleto",
}


def normalize_payment_method(value: str) -> str:
    normalized = normalize_text(value)
    if normalized not in PAYMENT_ALIASES:
        raise ValueError(f"Forma de pagamento desconhecida: {value}")
    return PAYMENT_ALIASES[normalized]


def max_installments(price: float) -> int:
    if price < MIN_PURCHASE_FOR_INSTALLMENTS:
        return 1
    maximum = 3
    for installments in range(4, 7):
        if price / installments >= MIN_INSTALLMENT_4X_6X:
            maximum = installments
    for installments in range(7, 13):
        if price / installments >= MIN_INSTALLMENT_7X_12X:
            maximum = installments
    return maximum


class PaymentService:
    def simulate(
        self,
        product: Product,
        forma: str,
        parcelas: int = 1,
    ) -> PaymentSimulation:
        method = normalize_payment_method(forma)
        table_price = round(float(product.price_brl), 2)
        base_price = round(float(product.effective_price or product.price_brl), 2)
        requested = max(1, min(int(parcelas), 12))
        observations: list[str] = []
        discount_pix_percent = 0.0
        discount_pix_value = 0.0
        final_price = base_price
        maximum = 1
        installment_value: float | None = None

        if product.has_active_promotion:
            observations.append("Promoções não são cumulativas com o desconto de PIX.")

        if method == "pix":
            if product.has_active_promotion:
                observations.append("O desconto de PIX não se aplica sobre preço promocional.")
            else:
                discount_pix_percent = PIX_DISCOUNT_PERCENT
                discount_pix_value = round(table_price * (PIX_DISCOUNT_PERCENT / 100), 2)
                final_price = round(table_price - discount_pix_value, 2)
                observations.append("Desconto de 5% do PIX aplicado sobre o preço de tabela.")
            message = f"No PIX, o valor fica {format_brl(final_price)}."
        elif method == "credito":
            maximum = max_installments(base_price)
            effective = min(requested, maximum)
            installment_value = round(base_price / effective, 2)
            if requested > maximum:
                observations.append(
                    f"Não é possível dividir em {requested}x. O máximo é {maximum}x."
                )
            if base_price < MIN_PURCHASE_FOR_INSTALLMENTS:
                observations.append("Compras abaixo de R$ 50,00 só podem ser pagas em 1x.")
            message = (
                f"Em {effective}x de {format_brl(installment_value)}, "
                f"o total fica {format_brl(base_price)}."
            )
        elif method == "debito":
            message = f"No débito, o valor é {format_brl(base_price)}."
            observations.append("Cartão de débito é aceito à vista, de todas as bandeiras.")
        else:
            message = f"No boleto, o valor é {format_brl(base_price)}."
            observations.append("O boleto compensa em até 3 dias úteis.")

        if base_price > COMBINATION_THRESHOLD:
            observations.append(
                "Combinação de formas de pagamento permitida para compras acima de R$ 2.000,00."
            )

        return PaymentSimulation(
            forma=method,
            preco_tabela=table_price,
            promocao_ativa=product.has_active_promotion,
            desconto_promocional_percent=product.discount_percent,
            preco_base=base_price,
            desconto_pix_percent=discount_pix_percent,
            desconto_pix_valor=discount_pix_value,
            preco_final=final_price,
            parcelas_solicitadas=requested,
            parcelas_maximas=maximum,
            valor_parcela=installment_value,
            total=final_price,
            permite_combinacao=base_price > COMBINATION_THRESHOLD,
            observacoes=observations,
            mensagem=message,
        )
