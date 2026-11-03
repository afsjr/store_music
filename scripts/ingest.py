from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date
from pathlib import Path

import pandas as pd

DATA_FILES = {
    "categories": "desafio_tecnico_ai_eng - categories.csv",
    "products": "desafio_tecnico_ai_eng - products.csv",
    "customers": "desafio_tecnico_ai_eng - customers.csv",
    "orders": "desafio_tecnico_ai_eng - orders.csv",
    "order_items": "desafio_tecnico_ai_eng - order_items.csv",
    "promotions": "desafio_tecnico_ai_eng - promotions.csv",
}
TRACKING_RE = re.compile(r"^BR[A-Z0-9]{9}BR$")
PRODUCT_STATUS = {"active", "discontinued", "coming_soon"}
ORDER_STATUS = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
COUNT_COLUMNS = ["categories", "products", "customers", "orders", "order_items", "promotions"]


def load_frames(data_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for key, filename in DATA_FILES.items():
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        frames[key] = pd.read_csv(path)
    return frames


def _parse_specs(value) -> dict:
    if pd.isna(value):
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def clean_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    categories = frames["categories"].copy()
    categories["category_id"] = categories["category_id"].astype(int)
    categories["name"] = categories["name"].astype(str).str.strip()
    categories["description"] = categories["description"].fillna("").astype(str).str.strip()

    products = frames["products"].copy()
    products["product_id"] = products["product_id"].astype(int)
    products["name"] = products["name"].astype(str).str.strip()
    products["price_brl"] = products["price_brl"].astype(float)
    products["category_id"] = products["category_id"].astype(int)
    products["description"] = products["description"].fillna("").astype(str).str.strip()
    products["stock_quantity"] = products["stock_quantity"].astype(int)
    products["status"] = products["status"].astype(str).str.strip()
    products["specs"] = products["specs"].apply(_parse_specs)
    products["created_at"] = pd.to_datetime(products["created_at"], errors="coerce").dt.date

    customers = frames["customers"].copy()
    customers["customer_id"] = customers["customer_id"].astype(int)
    for column in ["name", "phone", "email", "city"]:
        customers[column] = customers[column].astype(str).str.strip()

    orders = frames["orders"].copy()
    orders["order_id"] = orders["order_id"].astype(int)
    orders["customer_id"] = orders["customer_id"].astype(int)
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce").dt.date
    orders["status"] = orders["status"].astype(str).str.strip()
    orders["total_brl"] = orders["total_brl"].astype(float)
    orders["payment_method"] = orders["payment_method"].astype(str).str.strip()
    orders["tracking_code"] = orders["tracking_code"].where(orders["tracking_code"].notna(), None)
    orders["estimated_delivery"] = pd.to_datetime(
        orders["estimated_delivery"], errors="coerce"
    ).dt.date
    orders["notes"] = orders["notes"].where(orders["notes"].notna(), None)

    order_items = frames["order_items"].copy()
    order_items["order_id"] = order_items["order_id"].astype(int)
    order_items["product_id"] = order_items["product_id"].astype(int)
    order_items["quantity"] = order_items["quantity"].astype(int)

    promotions = frames["promotions"].copy()
    promotions["promotion_id"] = promotions["promotion_id"].astype(int)
    promotions["product_id"] = promotions["product_id"].astype(int)
    promotions["discount_percent"] = promotions["discount_percent"].astype(float)
    promotions["description"] = promotions["description"].astype(str).str.strip()
    promotions["is_active"] = promotions["is_active"].astype(int).astype(bool)

    return {
        "categories": categories,
        "products": products,
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
        "promotions": promotions,
    }


def validate_data(frames: dict[str, pd.DataFrame]) -> list[dict]:
    issues: list[dict] = []

    def add(severity: str, category: str, message: str) -> None:
        issues.append({"severity": severity, "category": category, "message": message})

    categories = frames["categories"]
    products = frames["products"]
    customers = frames["customers"]
    orders = frames["orders"]
    items = frames["order_items"]
    promotions = frames["promotions"]

    for name, frame, key in [
        ("categories", categories, "category_id"),
        ("products", products, "product_id"),
        ("customers", customers, "customer_id"),
        ("orders", orders, "order_id"),
        ("promotions", promotions, "promotion_id"),
    ]:
        duplicates = frame[frame.duplicated(key, keep=False)]
        if not duplicates.empty:
            add("critico", "pk", f"{name}: chaves duplicadas em {key}: {duplicates[key].tolist()}")

    missing_categories = set(products["category_id"]) - set(categories["category_id"])
    if missing_categories:
        add(
            "critico",
            "fk",
            f"products referencia categorias inexistentes: {sorted(missing_categories)}",
        )

    missing_customers = set(orders["customer_id"]) - set(customers["customer_id"])
    if missing_customers:
        add(
            "critico", "fk", f"orders referencia clientes inexistentes: {sorted(missing_customers)}"
        )

    missing_orders = set(items["order_id"]) - set(orders["order_id"])
    if missing_orders:
        add(
            "critico",
            "fk",
            f"order_items referencia pedidos inexistentes: {sorted(missing_orders)}",
        )

    missing_products = set(items["product_id"]) - set(products["product_id"])
    if missing_products:
        add(
            "critico",
            "fk",
            f"order_items referencia produtos inexistentes: {sorted(missing_products)}",
        )

    missing_promo_products = set(promotions["product_id"]) - set(products["product_id"])
    if missing_promo_products:
        add(
            "critico",
            "fk",
            f"promotions referencia produtos inexistentes: {sorted(missing_promo_products)}",
        )

    bad_product_status = set(products["status"]) - PRODUCT_STATUS
    if bad_product_status:
        add("critico", "status", f"Status de produto inválido: {sorted(bad_product_status)}")

    bad_order_status = set(orders["status"]) - ORDER_STATUS
    if bad_order_status:
        add("critico", "status", f"Status de pedido inválido: {sorted(bad_order_status)}")

    if (products["price_brl"] < 0).any():
        add("critico", "valor", "Existe produto com preço negativo.")
    if (products["stock_quantity"] < 0).any():
        add("critico", "valor", "Existe produto com estoque negativo.")
    if (items["quantity"] <= 0).any():
        add("critico", "valor", "Existe item de pedido com quantidade menor ou igual a zero.")
    if ((promotions["discount_percent"] < 0) | (promotions["discount_percent"] > 100)).any():
        add("critico", "valor", "Existe promoção com desconto fora de 0 a 100.")

    for code in orders["tracking_code"].dropna():
        if not TRACKING_RE.match(str(code)):
            add("aviso", "rastreio", f"Código de rastreio fora do padrão: {code}")

    duplicate_emails = customers[customers.duplicated("email", keep=False)]
    if not duplicate_emails.empty:
        add(
            "aviso",
            "duplicidade",
            "E-mails duplicados: "
            + ", ".join(
                f"{row.customer_id} ({row.email})" for row in duplicate_emails.itertuples()
            ),
        )

    zero_stock_active = products[
        (products["status"] == "active") & (products["stock_quantity"] == 0)
    ]
    if not zero_stock_active.empty:
        add(
            "aviso",
            "estoque",
            "Produtos ativos com estoque zero: "
            + ", ".join(str(v) for v in zero_stock_active["product_id"].tolist()),
        )

    price_map = products.set_index("product_id")["price_brl"]
    item_totals = items.copy()
    item_totals["line_total"] = item_totals["quantity"] * item_totals["product_id"].map(price_map)
    totals = item_totals.groupby("order_id")["line_total"].sum()
    merged = orders.set_index("order_id").join(totals.rename("items_total"))
    mismatches = merged[
        (merged["items_total"].notna())
        & ((merged["total_brl"] - merged["items_total"]).abs() > 0.01)
    ]
    if not mismatches.empty:
        for order_id, row in mismatches.iterrows():
            add(
                "aviso",
                "total",
                f"Pedido {order_id}: total cobrado {row.total_brl:.2f} difere da soma dos itens {row.items_total:.2f}.",
            )

    for product_id in range(135, 145):
        row = products[products["product_id"] == product_id]
        if not row.empty:
            add(
                "info",
                "descricao",
                f"Produto {product_id} possui nome e descrição potencialmente divergentes; manter o nome como fonte canônica.",
            )

    active_promos = promotions[promotions["is_active"]]
    if not active_promos.empty:
        add(
            "info",
            "promocao",
            "Promoções ativas: "
            + ", ".join(
                f"{row.product_id} ({row.discount_percent:.0f}%)"
                for row in active_promos.itertuples()
            ),
        )

    return issues


def counts_of(frames: dict[str, pd.DataFrame]) -> dict[str, int]:
    return {name: int(len(frames[name])) for name in COUNT_COLUMNS}


def write_report(counts: dict[str, int], issues: list[dict], path: Path, data_dir: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Relatório de Qualidade dos Dados",
        "",
        f"**Data:** {date.today().isoformat()}",
        f"**Diretório:** `{data_dir}`",
        "",
        "## Contagens",
        "",
        "| Arquivo | Registros |",
        "|---|---:|",
    ]
    for name, count in counts.items():
        lines.append(f"| {name} | {count} |")
    lines.extend(
        ["", "## Ocorrências", "", "| Severidade | Categoria | Descrição |", "|---|---|---|"]
    )
    if issues:
        for issue in issues:
            lines.append(f"| {issue['severity']} | {issue['category']} | {issue['message']} |")
    else:
        lines.append("| info | - | Nenhuma ocorrência encontrada. |")
    lines.extend(
        [
            "",
            "## Suposições de tratamento",
            "",
            "- Campos estruturados (`name`, `price_brl`, `stock_quantity`, `status`) prevalecem sobre descrições.",
            "- `is_active` indica promoção vigente; não há data de validade no CSV.",
            "- Produto ativo com estoque zero é tratado como indisponível temporariamente.",
            "- `orders.total_brl` é o valor cobrado, mesmo quando difere da soma dos itens.",
            "- E-mails duplicados não são mesclados.",
            "- Clientes não têm CEP; frete fora da região metropolitana fica sob cotação.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _upsert(frames: dict[str, pd.DataFrame], db_url: str, counts: dict[str, int]) -> None:
    import psycopg
    from psycopg.types.json import Json

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            conn.execute("insert into ingestion_runs (status) values ('running') returning id")
            categories = frames["categories"]
            conn.executemany(
                """
                insert into categories (category_id, name, description)
                values (%s, %s, %s)
                on conflict (category_id) do update set
                    name = excluded.name,
                    description = excluded.description
                """,
                [
                    (int(row.category_id), row.name, row.description)
                    for row in categories.itertuples()
                ],
            )
            products = frames["products"]
            conn.executemany(
                """
                insert into products (
                    product_id, name, price_brl, category_id, description,
                    stock_quantity, status, specs, created_at
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (product_id) do update set
                    name = excluded.name,
                    price_brl = excluded.price_brl,
                    category_id = excluded.category_id,
                    description = excluded.description,
                    stock_quantity = excluded.stock_quantity,
                    status = excluded.status,
                    specs = excluded.specs,
                    created_at = excluded.created_at
                """,
                [
                    (
                        int(row.product_id),
                        row.name,
                        float(row.price_brl),
                        int(row.category_id),
                        row.description,
                        int(row.stock_quantity),
                        row.status,
                        Json(row.specs),
                        row.created_at,
                    )
                    for row in products.itertuples()
                ],
            )
            customers = frames["customers"]
            conn.executemany(
                """
                insert into customers (customer_id, name, phone, email, city)
                values (%s, %s, %s, %s, %s)
                on conflict (customer_id) do update set
                    name = excluded.name,
                    phone = excluded.phone,
                    email = excluded.email,
                    city = excluded.city
                """,
                [
                    (int(row.customer_id), row.name, row.phone, row.email, row.city)
                    for row in customers.itertuples()
                ],
            )
            orders = frames["orders"]
            conn.executemany(
                """
                insert into orders (
                    order_id, customer_id, order_date, status, total_brl,
                    payment_method, tracking_code, estimated_delivery, notes
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (order_id) do update set
                    customer_id = excluded.customer_id,
                    order_date = excluded.order_date,
                    status = excluded.status,
                    total_brl = excluded.total_brl,
                    payment_method = excluded.payment_method,
                    tracking_code = excluded.tracking_code,
                    estimated_delivery = excluded.estimated_delivery,
                    notes = excluded.notes
                """,
                [
                    (
                        int(row.order_id),
                        int(row.customer_id),
                        row.order_date,
                        row.status,
                        float(row.total_brl),
                        row.payment_method,
                        None if pd.isna(row.tracking_code) else str(row.tracking_code),
                        None if pd.isna(row.estimated_delivery) else row.estimated_delivery,
                        None if pd.isna(row.notes) else str(row.notes),
                    )
                    for row in orders.itertuples()
                ],
            )
            items = frames["order_items"]
            conn.executemany(
                """
                insert into order_items (order_id, product_id, quantity)
                values (%s, %s, %s)
                on conflict (order_id, product_id) do update set
                    quantity = excluded.quantity
                """,
                [
                    (int(row.order_id), int(row.product_id), int(row.quantity))
                    for row in items.itertuples()
                ],
            )
            promotions = frames["promotions"]
            conn.executemany(
                """
                insert into promotions (promotion_id, product_id, discount_percent, description, is_active)
                values (%s, %s, %s, %s, %s)
                on conflict (promotion_id) do update set
                    product_id = excluded.product_id,
                    discount_percent = excluded.discount_percent,
                    description = excluded.description,
                    is_active = excluded.is_active
                """,
                [
                    (
                        int(row.promotion_id),
                        int(row.product_id),
                        float(row.discount_percent),
                        row.description,
                        bool(row.is_active),
                    )
                    for row in promotions.itertuples()
                ],
            )
            conn.execute(
                """
                update ingestion_runs
                set finished_at = now(), status = 'success', counts = %s
                where id = (
                    select id from ingestion_runs order by started_at desc limit 1
                )
                """,
                (Json(counts),),
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingere os CSVs no Supabase.")
    parser.add_argument("--data-dir", default="emporio_musica/data")
    parser.add_argument("--report", default="docs/data_quality_report.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    frames = clean_frames(load_frames(data_dir))
    counts = counts_of(frames)
    issues = validate_data(frames)
    write_report(counts, issues, Path(args.report), data_dir)

    print("Contagens:", counts)
    print("Ocorrências:", len(issues))
    print("Relatório:", Path(args.report).resolve())

    critical = [issue for issue in issues if issue["severity"] == "critico"]
    if critical:
        print("Validação bloqueada por ocorrências críticas:")
        for issue in critical:
            print("-", issue["message"])
        raise SystemExit(1)

    db_url = os.environ.get("SUPABASE_DB_URL")
    if args.dry_run or not db_url:
        if not db_url:
            print("SUPABASE_DB_URL ausente; execução em modo dry-run.")
        return

    _upsert(frames, db_url, counts)
    print("Ingestão concluída com sucesso.")


if __name__ == "__main__":
    main()
