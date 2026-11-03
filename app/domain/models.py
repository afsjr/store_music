from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProductStatus = Literal["active", "discontinued", "coming_soon"]
OrderStatus = Literal["pending", "confirmed", "shipped", "delivered", "cancelled"]
MessageRole = Literal["user", "assistant", "tool", "system"]


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)


class Category(DomainModel):
    category_id: int
    name: str
    description: str = ""


class Product(DomainModel):
    product_id: int
    name: str
    price_brl: float
    category_id: int
    category_name: str = ""
    description: str = ""
    stock_quantity: int = 0
    status: ProductStatus = "active"
    specs: dict[str, Any] = Field(default_factory=dict)
    created_at: date | None = None
    discount_percent: float | None = None
    effective_price: float | None = None
    has_active_promotion: bool = False

    @property
    def available(self) -> bool:
        return self.status == "active" and self.stock_quantity > 0


class Customer(DomainModel):
    customer_id: int
    name: str
    phone: str
    email: str
    city: str


class Order(DomainModel):
    order_id: int
    customer_id: int
    order_date: date
    status: OrderStatus
    total_brl: float
    payment_method: str
    tracking_code: str | None = None
    estimated_delivery: date | None = None
    notes: str | None = None


class OrderItem(DomainModel):
    order_id: int
    product_id: int
    quantity: int
    product_name: str = ""
    unit_price: float = 0.0


class Promotion(DomainModel):
    promotion_id: int
    product_id: int
    discount_percent: float
    description: str
    is_active: bool


class PolicyChunk(DomainModel):
    chunk_id: str
    section: str
    page: int
    content: str
    title: str = ""
    score: float = 0.0


class Citation(DomainModel):
    section: str
    page: int
    source: str = "Manual de Políticas"


class StoreInfo(DomainModel):
    trade_name: str
    legal_name: str
    cnpj: str
    address: str
    phone: str
    whatsapp: str
    email: str
    hours: dict[str, str]
    source: str = "Manual de Políticas v2.1"


class ReturnEligibility(DomainModel):
    reference_date: date
    receipt_date: date | None = None
    days_since_receipt: int | None = None
    days_since_purchase: int | None = None
    return_eligible: bool = False
    defect_eligible: bool = False
    legal_warranty_eligible: bool = False
    note: str = ""


class ShippingQuote(DomainModel):
    city: str
    subtotal: float
    kind: Literal["gratis", "fixo", "cotacao"]
    amount_brl: float | None = None
    message: str


class Message(DomainModel):
    role: MessageRole
    content: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime | None = None


class ToolCall(DomainModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(DomainModel):
    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    raw: dict[str, Any] | None = None


class ToolResult(DomainModel):
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    ok: bool = True
    error: str | None = None


class AgentReply(DomainModel):
    reply: str
    citations: list[Citation] = Field(default_factory=list)
    handoff: bool = False
    tool_calls: list[ToolResult] = Field(default_factory=list)
    session_id: str


class SessionInfo(DomainModel):
    session_id: str
    created_at: datetime


class Handoff(DomainModel):
    id: str
    conversation_id: str
    reason: str
    summary: str
    status: str = "aberto"
    created_at: datetime | None = None
    resolved_at: datetime | None = None
