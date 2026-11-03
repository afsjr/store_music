from __future__ import annotations


def test_search_violoes_under_1000(catalog):
    products = catalog.search(category="Violões", max_price=1000)
    assert products
    assert len(products) <= 10
    assert all(product.effective_price <= 1000 for product in products)
    assert all(product.category_name == "Violões" for product in products)
    assert all(product.available for product in products)


def test_takamine_price_and_pix(catalog):
    product = catalog.get(product_id=95)
    assert product is not None
    assert product.price_brl == 2199.0
    assert product.has_active_promotion is False
    assert catalog.pix_price(product) == 2089.05


def test_active_promotion_blocks_pix(catalog):
    product = catalog.get(product_id=127)
    assert product is not None
    assert product.has_active_promotion is True
    assert product.discount_percent == 10.0
    assert product.effective_price == 323.1
    assert catalog.pix_price(product) is None


def test_out_of_stock_product_is_unavailable(catalog):
    product = catalog.get(product_id=96)
    assert product is not None
    assert product.status == "active"
    assert product.stock_quantity == 0
    assert product.available is False


def test_discontinued_and_coming_soon(catalog):
    discontinued = catalog.get(product_id=113)
    coming_soon = catalog.get(product_id=130)
    assert discontinued is not None and discontinued.status == "discontinued"
    assert coming_soon is not None and coming_soon.status == "coming_soon"


def test_search_with_singular_category(catalog):
    products = catalog.search(category="violão", max_price=1000)
    assert products
    assert all(product.category_name == "Violões" for product in products)


def test_search_without_results(catalog):
    assert catalog.search(term="produto-que-nao-existe") == []


def test_product_detail_contains_specs(catalog):
    product = catalog.get(product_id=81)
    assert product is not None
    data = catalog.to_dict(product)
    assert data["nome"].startswith("Yamaha C40")
    assert data["specs"]["strings"] == "nylon"
    assert data["preco_tabela_formatado"].startswith("R$")
