from __future__ import annotations

from app.domain.models import Product
from app.domain.services.payments import PaymentService, max_installments


def _product(product_id: int, name: str, price: float) -> Product:
    return Product(
        product_id=product_id,
        name=name,
        price_brl=price,
        category_id=1,
        stock_quantity=1,
        effective_price=price,
    )


def test_max_installments_follows_policy_tiers():
    assert max_installments(49.90) == 1
    assert max_installments(50.0) == 3
    assert max_installments(323.10) == 4
    assert max_installments(500.0) == 6
    assert max_installments(799.90) == 7
    assert max_installments(1200.0) == 12


def test_pix_discount_without_promotion(catalog):
    product = catalog.get(product_id=95)
    simulation = PaymentService().simulate(product, "pix")
    assert simulation.preco_tabela == 2199.0
    assert simulation.desconto_pix_percent == 5.0
    assert simulation.desconto_pix_valor == 109.95
    assert simulation.preco_final == 2089.05
    assert simulation.parcelas_maximas == 1


def test_pix_does_not_stack_with_promotion(catalog):
    product = catalog.get(product_id=127)
    simulation = PaymentService().simulate(product, "pix")
    assert product.has_active_promotion is True
    assert simulation.preco_base == 323.10
    assert simulation.desconto_pix_percent == 0.0
    assert simulation.preco_final == 323.10


def test_debit_and_boleto_are_full_price(catalog):
    product = catalog.get(product_id=95)
    debit = PaymentService().simulate(product, "debito")
    boleto = PaymentService().simulate(product, "boleto")
    assert debit.preco_final == 2199.0
    assert boleto.preco_final == 2199.0
    assert any("3 dias úteis" in note for note in boleto.observacoes)


def test_credit_installments_and_tiers(catalog):
    product = catalog.get(product_id=95)
    simulation = PaymentService().simulate(product, "credito", parcelas=6)
    assert simulation.parcelas_solicitadas == 6
    assert simulation.parcelas_maximas == 12
    assert simulation.valor_parcela == 366.50
    assert simulation.total == 2199.0

    twelve = PaymentService().simulate(product, "credito", parcelas=12)
    assert twelve.valor_parcela == 183.25


def test_credit_caps_installments_and_reports_maximum(catalog):
    product = catalog.get(product_id=127)
    simulation = PaymentService().simulate(product, "credito", parcelas=5)
    assert simulation.parcelas_solicitadas == 5
    assert simulation.parcelas_maximas == 4
    assert simulation.valor_parcela == 80.78
    assert any("máximo é 4x" in note for note in simulation.observacoes)


def test_credit_below_50_is_single_payment():
    product = _product(999, "Palheta especial", 49.90)
    simulation = PaymentService().simulate(product, "credito", parcelas=3)
    assert simulation.parcelas_maximas == 1
    assert simulation.parcelas_solicitadas == 3
    assert simulation.valor_parcela == 49.90
    assert any("abaixo de R$ 50,00" in note for note in simulation.observacoes)


def test_combination_allowed_above_2000(catalog):
    expensive = PaymentService().simulate(catalog.get(product_id=95), "pix")
    cheap = PaymentService().simulate(catalog.get(product_id=127), "pix")
    assert expensive.permite_combinacao is True
    assert cheap.permite_combinacao is False


def test_tool_simulates_payment_by_product_id(tools):
    result = tools.execute(
        "simular_pagamento",
        {"produto_id": 95, "forma": "pix"},
        "sessao",
    )
    assert result.ok is True
    assert result.result["preco_final"] == 2089.05
    assert result.result["preco_final_formatado"] == "R$ 2.089,05"


def test_tool_simulates_credit_by_name(tools):
    result = tools.execute(
        "simular_pagamento",
        {"nome": "Takamine GD20", "forma": "credito", "parcelas": 6},
        "sessao",
    )
    assert result.ok is True
    assert result.result["valor_parcela"] == 366.50
    assert result.result["parcelas_maximas"] == 12


def test_tool_reports_missing_product(tools):
    result = tools.execute(
        "simular_pagamento",
        {"produto_id": 99999, "forma": "pix"},
        "sessao",
    )
    assert result.ok is True
    assert result.result["erro"] == "Produto não encontrado."


def test_tool_rejects_invalid_payment_method(tools):
    result = tools.execute(
        "simular_pagamento",
        {"produto_id": 95, "forma": "cheque"},
        "sessao",
    )
    assert result.ok is False
    assert result.error == "validation_error"
