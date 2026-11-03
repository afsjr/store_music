from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.domain.models import (
    Customer,
    Handoff,
    LLMResponse,
    Message,
    Order,
    OrderItem,
    PolicyChunk,
    Product,
    Promotion,
    SessionInfo,
    StoreInfo,
)


class CatalogRepository(Protocol):
    def search_products(
        self,
        term: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool = True,
        limit: int = 10,
    ) -> list[Product]: ...

    def get_product(
        self, product_id: int | None = None, name: str | None = None
    ) -> Product | None: ...

    def list_categories(self) -> list[tuple[int, str]]: ...


class PromotionRepository(Protocol):
    def active_promotion(self, product_id: int) -> Promotion | None: ...


class CustomerRepository(Protocol):
    def find_customer(self, name: str, contact: str) -> list[Customer]: ...

    def get_customer(self, customer_id: int) -> Customer | None: ...


class OrderRepository(Protocol):
    def list_orders_by_customer(self, customer_id: int) -> list[Order]: ...

    def get_order(self, order_id: int) -> Order | None: ...

    def get_order_items(self, order_id: int) -> list[OrderItem]: ...


class ConversationRepository(Protocol):
    def create_session(self) -> SessionInfo: ...

    def get_or_create_session(self, session_id: str | None) -> SessionInfo: ...

    def session_exists(self, session_id: str) -> bool: ...

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        citations: list[dict] | None = None,
    ) -> Message: ...

    def list_messages(self, session_id: str, limit: int = 50) -> list[Message]: ...

    def record_handoff(self, session_id: str, reason: str, summary: str) -> Handoff: ...


class PolicyRetriever(Protocol):
    def search(self, query: str, k: int = 3) -> list[PolicyChunk]: ...


class StoreInfoProvider(Protocol):
    def get_store_info(self) -> StoreInfo: ...


class LLMClient(Protocol):
    def complete(self, messages: Sequence[dict], tools: Sequence[dict]) -> LLMResponse: ...
