from __future__ import annotations

import uuid

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from app.domain.models import (
    Citation,
    Customer,
    Handoff,
    Message,
    Order,
    OrderItem,
    Product,
    Promotion,
    SessionInfo,
    StoreInfo,
)
from app.domain.store_info import STORE_INFO


class SupabaseStore:
    """Repositórios SQL para o Supabase Postgres."""

    def __init__(self, db_url: str) -> None:
        if not db_url:
            raise ValueError("SUPABASE_DB_URL não configurada.")
        self.db_url = db_url
        with self._connect() as conn:
            conn.execute("select 1")

    def _connect(self):
        return psycopg.connect(self.db_url, autocommit=True, row_factory=dict_row)

    def _product_from_row(self, row: dict) -> Product:
        return Product(
            product_id=row["product_id"],
            name=row["name"],
            price_brl=float(row["price_brl"]),
            category_id=row["category_id"],
            category_name=row.get("category_name") or "",
            description=row.get("description") or "",
            stock_quantity=row.get("stock_quantity") or 0,
            status=row.get("status") or "active",
            specs=row.get("specs") or {},
            created_at=row.get("created_at"),
            effective_price=float(row["price_brl"]),
        )

    def _enrich_products(self, products: list[Product]) -> list[Product]:
        if not products:
            return products
        ids = [p.product_id for p in products]
        with self._connect() as conn:
            rows = conn.execute(
                """
                select distinct on (product_id)
                    product_id, promotion_id, discount_percent, description, is_active
                from promotions
                where product_id = any(%s) and is_active
                order by product_id, discount_percent desc
                """,
                (ids,),
            ).fetchall()
        promos = {row["product_id"]: row for row in rows}
        enriched: list[Product] = []
        for product in products:
            promo = promos.get(product.product_id)
            if promo:
                effective = round(
                    product.price_brl * (1 - float(promo["discount_percent"]) / 100), 2
                )
                enriched.append(
                    product.model_copy(
                        update={
                            "discount_percent": float(promo["discount_percent"]),
                            "effective_price": effective,
                            "has_active_promotion": True,
                        }
                    )
                )
            else:
                enriched.append(product)
        return enriched

    def search_products(
        self,
        term: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool = True,
        limit: int = 10,
    ) -> list[Product]:
        where = ["1=1"]
        params: list = []
        if in_stock:
            where.append("p.status = 'active' and p.stock_quantity > 0")
        if min_price is not None:
            where.append("p.price_brl >= %s")
            params.append(min_price)
        if max_price is not None:
            where.append("p.price_brl <= %s")
            params.append(max_price)
        if category:
            where.append(
                "(p.category_id::text = %s or unaccent(lower(c.name)) like unaccent(lower(%s)))"
            )
            params.extend([category, f"%{category}%"])
        if term:
            where.append(
                "unaccent(lower(p.name || ' ' || coalesce(p.description, '') || ' ' || "
                "coalesce(p.specs::text, ''))) like unaccent(lower(%s))"
            )
            params.append(f"%{term}%")
        params.append(max(1, min(limit, 50)))
        sql = f"""
            select p.product_id, p.name, p.price_brl, p.category_id, p.description,
                   p.stock_quantity, p.status, p.specs, p.created_at,
                   c.name as category_name
            from products p
            join categories c on c.category_id = p.category_id
            where {" and ".join(where)}
            order by p.price_brl, p.name
            limit %s
        """
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return self._enrich_products([self._product_from_row(row) for row in rows])

    def get_product(self, product_id: int | None = None, name: str | None = None) -> Product | None:
        where = "1=1"
        params: list = []
        if product_id is not None:
            where = "p.product_id = %s"
            params.append(product_id)
        elif name:
            where = "unaccent(lower(p.name)) like unaccent(lower(%s))"
            params.append(f"%{name}%")
        else:
            return None
        sql = f"""
            select p.product_id, p.name, p.price_brl, p.category_id, p.description,
                   p.stock_quantity, p.status, p.specs, p.created_at,
                   c.name as category_name
            from products p
            join categories c on c.category_id = p.category_id
            where {where}
            order by p.product_id
            limit 1
        """
        with self._connect() as conn:
            row = conn.execute(sql, params).fetchone()
        if not row:
            return None
        products = self._enrich_products([self._product_from_row(row)])
        return products[0]

    def list_categories(self) -> list[tuple[int, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "select category_id, name from categories order by category_id"
            ).fetchall()
        return [(row["category_id"], row["name"]) for row in rows]

    def active_promotion(self, product_id: int) -> Promotion | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                select promotion_id, product_id, discount_percent, description, is_active
                from promotions
                where product_id = %s and is_active
                order by discount_percent desc
                limit 1
                """,
                (product_id,),
            ).fetchone()
        if not row:
            return None
        return Promotion(
            promotion_id=row["promotion_id"],
            product_id=row["product_id"],
            discount_percent=float(row["discount_percent"]),
            description=row["description"],
            is_active=row["is_active"],
        )

    def find_customer(self, name: str, contact: str) -> list[Customer]:
        digits = "".join(ch for ch in contact if ch.isdigit())
        with self._connect() as conn:
            rows = conn.execute(
                """
                select customer_id, name, phone, email, city
                from customers
                where unaccent(lower(name)) like unaccent(lower(%s))
                  and (
                    lower(email) = lower(%s)
                    or (%s <> '' and regexp_replace(phone, '\\D', '', 'g') = %s)
                  )
                order by customer_id
                """,
                (f"%{name}%", contact, digits, digits),
            ).fetchall()
        return [Customer(**row) for row in rows]

    def get_customer(self, customer_id: int) -> Customer | None:
        with self._connect() as conn:
            row = conn.execute(
                "select customer_id, name, phone, email, city from customers where customer_id = %s",
                (customer_id,),
            ).fetchone()
        return Customer(**row) if row else None

    def list_orders_by_customer(self, customer_id: int) -> list[Order]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select order_id, customer_id, order_date, status, total_brl, payment_method,
                       tracking_code, estimated_delivery, notes
                from orders
                where customer_id = %s
                order by order_date desc, order_id desc
                """,
                (customer_id,),
            ).fetchall()
        return [Order(**row) for row in rows]

    def get_order(self, order_id: int) -> Order | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                select order_id, customer_id, order_date, status, total_brl, payment_method,
                       tracking_code, estimated_delivery, notes
                from orders
                where order_id = %s
                """,
                (order_id,),
            ).fetchone()
        return Order(**row) if row else None

    def get_order_items(self, order_id: int) -> list[OrderItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select oi.order_id, oi.product_id, oi.quantity, p.name as product_name,
                       coalesce(po.effective_price, p.price_brl) as unit_price
                from order_items oi
                join products p on p.product_id = oi.product_id
                left join product_offers po on po.product_id = p.product_id
                where oi.order_id = %s
                order by oi.product_id
                """,
                (order_id,),
            ).fetchall()
        return [OrderItem(**row) for row in rows]

    # Conversas ---------------------------------------------------------------
    def create_session(self) -> SessionInfo:
        session_id = str(uuid.uuid4())
        with self._connect() as conn:
            row = conn.execute(
                """
                insert into conversations (session_id)
                values (%s)
                returning session_id, created_at
                """,
                (session_id,),
            ).fetchone()
        return SessionInfo(session_id=row["session_id"], created_at=row["created_at"])

    def get_or_create_session(self, session_id: str | None) -> SessionInfo:
        if session_id:
            with self._connect() as conn:
                row = conn.execute(
                    "select session_id, created_at from conversations where session_id = %s",
                    (session_id,),
                ).fetchone()
            if row:
                return SessionInfo(session_id=row["session_id"], created_at=row["created_at"])
            with self._connect() as conn:
                row = conn.execute(
                    """
                    insert into conversations (session_id)
                    values (%s)
                    on conflict (session_id) do update set updated_at = now()
                    returning session_id, created_at
                    """,
                    (session_id,),
                ).fetchone()
            return SessionInfo(session_id=row["session_id"], created_at=row["created_at"])
        return self.create_session()

    def session_exists(self, session_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "select 1 from conversations where session_id = %s", (session_id,)
            ).fetchone()
        return bool(row)

    def _conversation_id(self, session_id: str) -> str:
        session = self.get_or_create_session(session_id)
        with self._connect() as conn:
            row = conn.execute(
                "select id from conversations where session_id = %s",
                (session.session_id,),
            ).fetchone()
        return str(row["id"])

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        citations: list[dict] | None = None,
    ) -> Message:
        conversation_id = self._conversation_id(session_id)
        with self._connect() as conn:
            row = conn.execute(
                """
                insert into messages (conversation_id, role, content, tool_calls, citations)
                values (%s, %s, %s, %s, %s)
                returning role, content, tool_calls, citations, created_at
                """,
                (
                    conversation_id,
                    role,
                    content,
                    Json(tool_calls or []),
                    Json(citations or []),
                ),
            ).fetchone()
        return Message(
            role=row["role"],
            content=row["content"],
            tool_calls=row["tool_calls"] or [],
            citations=[Citation(**c) for c in (row["citations"] or [])],
            created_at=row["created_at"],
        )

    def list_messages(self, session_id: str, limit: int = 50) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select m.role, m.content, m.tool_calls, m.citations, m.created_at
                from messages m
                join conversations c on c.id = m.conversation_id
                where c.session_id = %s
                order by m.created_at asc, m.id asc
                limit %s
                """,
                (session_id, max(1, min(limit, 200))),
            ).fetchall()
        return [
            Message(
                role=row["role"],
                content=row["content"],
                tool_calls=row["tool_calls"] or [],
                citations=[Citation(**c) for c in (row["citations"] or [])],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def record_handoff(self, session_id: str, reason: str, summary: str) -> Handoff:
        conversation_id = self._conversation_id(session_id)
        with self._connect() as conn:
            row = conn.execute(
                """
                insert into handoffs (conversation_id, reason, summary)
                values (%s, %s, %s)
                returning id, conversation_id, reason, summary, status, created_at, resolved_at
                """,
                (conversation_id, reason, summary),
            ).fetchone()
        return Handoff(
            id=str(row["id"]),
            conversation_id=str(row["conversation_id"]),
            reason=row["reason"],
            summary=row["summary"],
            status=row["status"],
            created_at=row["created_at"],
            resolved_at=row["resolved_at"],
        )

    def get_store_info(self) -> StoreInfo:
        with self._connect() as conn:
            rows = conn.execute("select key, value from store_info").fetchall()
        values = {row["key"]: row["value"] for row in rows}
        return STORE_INFO.model_copy(
            update={
                "address": values.get("endereco", STORE_INFO.address),
                "phone": values.get("telefone", STORE_INFO.phone),
                "whatsapp": values.get("whatsapp", STORE_INFO.whatsapp),
                "email": values.get("email", STORE_INFO.email),
                "hours": {
                    "segunda_a_sexta": values.get(
                        "horario_segunda_sexta", STORE_INFO.hours["segunda_a_sexta"]
                    ),
                    "sabado": values.get("horario_sabado", STORE_INFO.hours["sabado"]),
                    "domingo_e_feriados": values.get(
                        "horario_domingo_feriados", STORE_INFO.hours["domingo_e_feriados"]
                    ),
                },
            }
        )

    def touch_session(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "update conversations set updated_at = now() where session_id = %s",
                (session_id,),
            )
