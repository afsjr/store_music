from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.domain.models import (
    Customer,
    Handoff,
    Message,
    Order,
    OrderItem,
    PolicyChunk,
    Product,
    Promotion,
    SessionInfo,
    StoreInfo,
)
from app.domain.store_info import STORE_INFO
from app.domain.text import digits_only, normalize_text


def _parse_date(value: Any) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _parse_float(value: Any, default: float = 0.0) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value: Any, default: int = 0) -> int:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_specs(value: Any) -> dict[str, Any]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


class InMemoryStore:
    """Carrega os CSVs e mantém conversas em memória."""

    def __init__(self, data_dir: str | Path, store_today: date | None = None) -> None:
        self.data_dir = Path(data_dir)
        self.store_today = store_today or date.today()
        self.categories: dict[int, str] = {}
        self.products: dict[int, Product] = {}
        self.customers: dict[int, Customer] = {}
        self.orders: dict[int, Order] = {}
        self.order_items: dict[int, list[OrderItem]] = {}
        self.promotions: list[Promotion] = []
        self._sessions: dict[str, SessionInfo] = {}
        self._messages: dict[str, list[Message]] = {}
        self._handoffs: list[Handoff] = []
        self._load()

    def _read(self, filename: str) -> pd.DataFrame:
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}")
        return pd.read_csv(path)

    def _load(self) -> None:
        categories = self._read("desafio_tecnico_ai_eng - categories.csv")
        for _, row in categories.iterrows():
            self.categories[int(row["category_id"])] = str(row["name"])

        products = self._read("desafio_tecnico_ai_eng - products.csv")
        for _, row in products.iterrows():
            product = Product(
                product_id=int(row["product_id"]),
                name=str(row["name"]).strip(),
                price_brl=_parse_float(row["price_brl"]),
                category_id=_parse_int(row["category_id"]),
                category_name=self.categories.get(_parse_int(row["category_id"]), ""),
                description=str(row.get("description") or "").strip(),
                stock_quantity=_parse_int(row["stock_quantity"]),
                status=str(row.get("status") or "active").strip(),
                specs=_parse_specs(row.get("specs")),
                created_at=_parse_date(row.get("created_at")),
            )
            product.effective_price = product.price_brl
            self.products[product.product_id] = product

        customers = self._read("desafio_tecnico_ai_eng - customers.csv")
        for _, row in customers.iterrows():
            customer = Customer(
                customer_id=int(row["customer_id"]),
                name=str(row["name"]).strip(),
                phone=str(row["phone"]).strip(),
                email=str(row["email"]).strip(),
                city=str(row["city"]).strip(),
            )
            self.customers[customer.customer_id] = customer

        promotions = self._read("desafio_tecnico_ai_eng - promotions.csv")
        for _, row in promotions.iterrows():
            self.promotions.append(
                Promotion(
                    promotion_id=int(row["promotion_id"]),
                    product_id=int(row["product_id"]),
                    discount_percent=_parse_float(row["discount_percent"]),
                    description=str(row["description"]).strip(),
                    is_active=bool(int(row["is_active"])),
                )
            )
        for product in self.products.values():
            promo = self.active_promotion(product.product_id)
            if promo:
                product.discount_percent = promo.discount_percent
                product.effective_price = round(
                    product.price_brl * (1 - promo.discount_percent / 100), 2
                )
                product.has_active_promotion = True

        orders = self._read("desafio_tecnico_ai_eng - orders.csv")
        for _, row in orders.iterrows():
            order = Order(
                order_id=int(row["order_id"]),
                customer_id=int(row["customer_id"]),
                order_date=_parse_date(row["order_date"]) or date.today(),
                status=str(row["status"]).strip(),
                total_brl=_parse_float(row["total_brl"]),
                payment_method=str(row["payment_method"]).strip(),
                tracking_code=(
                    None if pd.isna(row.get("tracking_code")) else str(row["tracking_code"]).strip()
                ),
                estimated_delivery=_parse_date(row.get("estimated_delivery")),
                notes=None if pd.isna(row.get("notes")) else str(row["notes"]).strip(),
            )
            self.orders[order.order_id] = order

        items = self._read("desafio_tecnico_ai_eng - order_items.csv")
        for _, row in items.iterrows():
            order_id = int(row["order_id"])
            product_id = int(row["product_id"])
            product = self.products.get(product_id)
            self.order_items.setdefault(order_id, []).append(
                OrderItem(
                    order_id=order_id,
                    product_id=product_id,
                    quantity=_parse_int(row["quantity"], 1),
                    product_name=product.name if product else f"Produto {product_id}",
                    unit_price=product.effective_price if product else 0.0,
                )
            )

    # Catálogo -----------------------------------------------------------------
    def search_products(
        self,
        term: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool = True,
        limit: int = 10,
    ) -> list[Product]:
        term_norm = normalize_text(term)
        category_norm = normalize_text(category)
        result: list[Product] = []
        for product in self.products.values():
            if in_stock and not product.available:
                continue
            if min_price is not None and product.effective_price < min_price:
                continue
            if max_price is not None and product.effective_price > max_price:
                continue
            if category_norm:
                category_id_match = category_norm.isdigit() and product.category_id == int(
                    category_norm
                )
                category_name_match = category_norm in normalize_text(product.category_name)
                if not (category_id_match or category_name_match):
                    continue
            if term_norm:
                haystack_parts = [
                    product.name,
                    product.description,
                    product.category_name,
                    " ".join(str(v) for v in product.specs.values()),
                ]
                haystack = normalize_text(" ".join(haystack_parts))
                if term_norm not in haystack:
                    continue
            result.append(product)
        result.sort(key=lambda p: (not p.available, p.effective_price, p.name))
        return result[: max(1, min(limit, 50))]

    def get_product(self, product_id: int | None = None, name: str | None = None) -> Product | None:
        if product_id is not None:
            return self.products.get(product_id)
        if not name:
            return None
        target = normalize_text(name)
        exact = [p for p in self.products.values() if normalize_text(p.name) == target]
        if exact:
            return exact[0]
        partial = [p for p in self.products.values() if target in normalize_text(p.name)]
        return partial[0] if partial else None

    def list_categories(self) -> list[tuple[int, str]]:
        return sorted(self.categories.items())

    # Promoções ---------------------------------------------------------------
    def active_promotion(self, product_id: int) -> Promotion | None:
        active = [
            promo for promo in self.promotions if promo.product_id == product_id and promo.is_active
        ]
        if not active:
            return None
        return max(active, key=lambda p: p.discount_percent)

    # Clientes ----------------------------------------------------------------
    def find_customer(self, name: str, contact: str) -> list[Customer]:
        target_name = normalize_text(name)
        contact_norm = normalize_text(contact)
        contact_digits = digits_only(contact)
        matches: list[Customer] = []
        for customer in self.customers.values():
            name_ok = target_name == normalize_text(customer.name) or target_name in normalize_text(
                customer.name
            )
            if not name_ok:
                continue
            email_ok = contact_norm and contact_norm == normalize_text(customer.email)
            phone_ok = contact_digits and contact_digits == digits_only(customer.phone)
            if email_ok or phone_ok:
                matches.append(customer)
        return matches

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.customers.get(customer_id)

    # Pedidos -----------------------------------------------------------------
    def list_orders_by_customer(self, customer_id: int) -> list[Order]:
        orders = [o for o in self.orders.values() if o.customer_id == customer_id]
        orders.sort(key=lambda o: o.order_date, reverse=True)
        return orders

    def get_order(self, order_id: int) -> Order | None:
        return self.orders.get(order_id)

    def get_order_items(self, order_id: int) -> list[OrderItem]:
        return list(self.order_items.get(order_id, []))

    # Conversas ---------------------------------------------------------------
    def create_session(self) -> SessionInfo:
        session = SessionInfo(
            session_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
        )
        self._sessions[session.session_id] = session
        self._messages[session.session_id] = []
        return session

    def get_or_create_session(self, session_id: str | None) -> SessionInfo:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        session = SessionInfo(
            session_id=session_id or str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
        )
        self._sessions[session.session_id] = session
        self._messages.setdefault(session.session_id, [])
        return session

    def session_exists(self, session_id: str) -> bool:
        return session_id in self._sessions

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        citations: list[dict] | None = None,
    ) -> Message:
        session = self.get_or_create_session(session_id)
        message = Message(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            citations=citations or [],
            created_at=datetime.now(timezone.utc),
        )
        self._messages.setdefault(session.session_id, []).append(message)
        return message

    def list_messages(self, session_id: str, limit: int = 50) -> list[Message]:
        messages = self._messages.get(session_id, [])
        return messages[-limit:]

    def record_handoff(self, session_id: str, reason: str, summary: str) -> Handoff:
        session = self.get_or_create_session(session_id)
        handoff = Handoff(
            id=str(uuid.uuid4()),
            conversation_id=session.session_id,
            reason=reason,
            summary=summary,
            status="aberto",
            created_at=datetime.now(timezone.utc),
        )
        self._handoffs.append(handoff)
        return handoff

    def get_store_info(self) -> StoreInfo:
        return STORE_INFO

    # Auxiliar para testes ----------------------------------------------------
    def all_products(self) -> list[Product]:
        return list(self.products.values())

    def policy_chunks_unused(self) -> list[PolicyChunk]:
        return []
