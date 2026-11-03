from __future__ import annotations


def test_expired_promotion_is_recoverable(catalog):
    promotions = catalog.promotions_for_product(95)
    assert len(promotions) == 1
    assert promotions[0].is_active is False

    expired = catalog.expired_promotion(95)
    assert expired is not None
    assert expired.promotion_id == 4
    assert expired.discount_percent == 12


def test_active_promotion_shows_original_percent_and_final_price(tools):
    result = tools.execute("consultar_promocao", {"produto_id": 127}, "sessao")
    assert result.ok is True
    data = result.result
    assert data["promocao"]["desconto_percentual"] == 10
    assert data["promocao"]["preco_original"] == 359.0
    assert data["promocao"]["preco_promocional"] == 323.10
    assert data["preco_pix"] is None
    assert "não são cumulativas" in data["mensagem"]


def test_expired_promotion_reports_current_price_without_rain_check(tools):
    result = tools.execute("consultar_promocao", {"produto_id": 95}, "sessao")
    assert result.ok is True
    data = result.result
    assert "promocao" not in data
    assert data["promocao_expirada"]["desconto_percentual"] == 12
    assert data["preco_atual"] == 2199.0
    assert data["preco_atual_formatado"] == "R$ 2.199,00"
    assert "expirou" in data["mensagem"]
    assert "rain check" in data["mensagem"]


def test_product_without_promotion_history(tools):
    result = tools.execute("consultar_promocao", {"produto_id": 81}, "sessao")
    assert result.ok is True
    data = result.result
    assert "promocao" not in data
    assert "promocao_expirada" not in data
    assert "Não há promoção" in data["mensagem"]
