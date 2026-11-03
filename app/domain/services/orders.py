from __future__ import annotations

from datetime import date

from app.domain.format import format_brl, format_date
from app.domain.models import Customer, Order, ReturnEligibility
from app.domain.ports import CustomerRepository, OrderRepository
from app.logging import mask_email, mask_phone

STATUS_LABELS = {
    "pending": "aguardando confirmação",
    "confirmed": "confirmado",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}

PAYMENT_LABELS = {
    "pix": "PIX",
    "debit": "cartão de débito",
    "boleto": "boleto bancário",
    "credit_3x": "cartão de crédito em 3x",
    "credit_6x": "cartão de crédito em 6x",
    "credit_12x": "cartão de crédito em 12x",
}


class OrderService:
    def __init__(
        self,
        customers: CustomerRepository,
        orders: OrderRepository,
        today: date,
    ) -> None:
        self.customers = customers
        self.orders = orders
        self.today = today

    def identify(self, name: str, contact: str) -> list[Customer]:
        return self.customers.find_customer(name=name, contact=contact)

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.customers.get_customer(customer_id)

    def list_orders(self, customer_id: int) -> list[Order]:
        return self.orders.list_orders_by_customer(customer_id)

    def _receipt_date(self, order: Order) -> date | None:
        if order.status != "delivered":
            return None
        return order.estimated_delivery or order.order_date

    def return_eligibility(self, order: Order) -> ReturnEligibility:
        receipt = self._receipt_date(order)
        days_receipt = (self.today - receipt).days if receipt else None
        days_purchase = (self.today - order.order_date).days
        delivered = order.status == "delivered"
        return_eligible = bool(delivered and days_receipt is not None and 0 <= days_receipt <= 7)
        defect_eligible = bool(delivered and 0 <= days_purchase <= 30)
        warranty_eligible = bool(delivered and days_receipt is not None and 0 <= days_receipt <= 90)
        if not delivered:
            note = "O pedido ainda não foi entregue; os prazos contam a partir do recebimento."
        elif receipt is None:
            note = "Data de recebimento não informada; usei a data do pedido como referência."
        else:
            note = "Prazos calculados a partir da data de recebimento registrada no pedido."
        return ReturnEligibility(
            reference_date=self.today,
            receipt_date=receipt,
            days_since_receipt=days_receipt,
            days_since_purchase=days_purchase,
            return_eligible=return_eligible,
            defect_eligible=defect_eligible,
            legal_warranty_eligible=warranty_eligible,
            note=note,
        )

    def order_details(self, order_id: int, customer_id: int) -> dict | None:
        order = self.orders.get_order(order_id)
        if order is None or order.customer_id != customer_id:
            return None
        customer = self.customers.get_customer(order.customer_id)
        items = self.orders.get_order_items(order_id)
        eligibility = self.return_eligibility(order)
        return {
            "pedido": {
                "order_id": order.order_id,
                "data_pedido": format_date(order.order_date),
                "status": order.status,
                "status_label": STATUS_LABELS.get(order.status, order.status),
                "total_brl": order.total_brl,
                "total_formatado": format_brl(order.total_brl),
                "forma_pagamento": PAYMENT_LABELS.get(order.payment_method, order.payment_method),
                "rastreio": order.tracking_code,
                "previsao_entrega": format_date(order.estimated_delivery),
                "observacoes": order.notes,
            },
            "cliente": {
                "customer_id": customer.customer_id if customer else None,
                "nome": customer.name if customer else "Cliente",
                "telefone": mask_phone(customer.phone) if customer else "não informado",
                "email": mask_email(customer.email) if customer else "não informado",
                "cidade": customer.city if customer else "",
            },
            "itens": [
                {
                    "product_id": item.product_id,
                    "nome": item.product_name,
                    "quantidade": item.quantity,
                    "preco_unitario": item.unit_price,
                    "preco_unitario_formatado": format_brl(item.unit_price),
                }
                for item in items
            ],
            "prazos": eligibility.model_dump(mode="json"),
        }

    def customer_to_dict(self, customer: Customer) -> dict:
        return {
            "customer_id": customer.customer_id,
            "nome": customer.name,
            "telefone": mask_phone(customer.phone),
            "email": mask_email(customer.email),
            "cidade": customer.city,
        }
