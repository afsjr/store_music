from __future__ import annotations


def test_identify_customer(orders):
    matches = orders.identify("Ana Carolina Ferreira", "(67) 99654-7821")
    assert len(matches) == 1
    assert matches[0].customer_id == 2


def test_identify_customer_by_email(orders):
    matches = orders.identify("Ana Carolina Ferreira", "anacarol.ferreira@coldmail.com")
    assert len(matches) == 1
    assert matches[0].customer_id == 2


def test_order_details_for_owner(orders):
    details = orders.order_details(8, 2)
    assert details is not None
    assert details["pedido"]["status"] == "shipped"
    assert details["pedido"]["rastreio"] == "BRJL5544332BR"
    assert details["cliente"]["customer_id"] == 2
    assert details["cliente"]["telefone"] == "****7821"
    assert details["cliente"]["email"].startswith("a***@")


def test_order_details_denies_other_customer(orders):
    assert orders.order_details(8, 7) is None


def test_return_eligibility_within_seven_days(orders):
    details = orders.order_details(7, 14)
    assert details is not None
    prazos = details["prazos"]
    assert prazos["receipt_date"] == "2026-02-17"
    assert prazos["days_since_receipt"] == 3
    assert prazos["return_eligible"] is True


def test_return_eligibility_for_shipped_order(orders):
    details = orders.order_details(8, 2)
    assert details is not None
    assert details["prazos"]["return_eligible"] is False
    assert "ainda não foi entregue" in details["prazos"]["note"]


def test_old_order_is_outside_return_window(orders):
    details = orders.order_details(1, 3)
    assert details is not None
    assert details["prazos"]["return_eligible"] is False
