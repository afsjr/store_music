from __future__ import annotations


def test_alternatives_for_out_of_stock_product(catalog):
    target = catalog.get(product_id=96)
    alternatives = catalog.alternatives(96, limit=3)
    assert target is not None
    assert target.available is False
    assert 1 <= len(alternatives) <= 3
    assert all(item.product_id != 96 for item in alternatives)
    assert all(item.category_id == target.category_id for item in alternatives)
    assert all(item.available for item in alternatives)


def test_alternatives_are_sorted_by_price_proximity(catalog):
    target = catalog.get(product_id=96)
    alternatives = catalog.alternatives(96, limit=5)
    distances = [
        abs((item.effective_price or item.price_brl) - target.price_brl) for item in alternatives
    ]
    assert distances == sorted(distances)


def test_alternatives_tool_for_out_of_stock(tools):
    result = tools.execute("buscar_alternativas", {"produto_id": 96}, "sessao")
    assert result.ok is True
    data = result.result
    assert data["quantidade"] == len(data["alternativas"])
    assert 1 <= data["quantidade"] <= 3
    assert "indisponível" in data["mensagem"]
    assert all(item["disponivel"] for item in data["alternativas"])


def test_alternatives_tool_for_discontinued(tools):
    result = tools.execute("buscar_alternativas", {"produto_id": 113}, "sessao")
    assert result.ok is True
    assert result.result["produto"]["status"] == "discontinued"
    assert result.result["alternativas"]


def test_alternatives_tool_respects_limit(tools):
    result = tools.execute(
        "buscar_alternativas",
        {"produto_id": 96, "limite": 1},
        "sessao",
    )
    assert result.ok is True
    assert len(result.result["alternativas"]) == 1


def test_alternatives_tool_reports_missing_product(tools):
    result = tools.execute("buscar_alternativas", {"produto_id": 99999}, "sessao")
    assert result.ok is True
    assert result.result["erro"] == "Produto não encontrado."
