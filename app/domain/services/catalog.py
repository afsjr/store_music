from __future__ import annotations

from app.domain.format import format_brl
from app.domain.models import Product, Promotion
from app.domain.ports import CatalogRepository, PromotionRepository


class CatalogService:
    def __init__(
        self,
        catalog: CatalogRepository,
        promotions: PromotionRepository,
    ) -> None:
        self.catalog = catalog
        self.promotions = promotions

    def _enrich(self, product: Product) -> Product:
        promo = self.promotions.active_promotion(product.product_id)
        if promo:
            effective = round(product.price_brl * (1 - promo.discount_percent / 100), 2)
            return product.model_copy(
                update={
                    "discount_percent": promo.discount_percent,
                    "effective_price": effective,
                    "has_active_promotion": True,
                }
            )
        return product.model_copy(
            update={
                "discount_percent": None,
                "effective_price": product.price_brl,
                "has_active_promotion": False,
            }
        )

    def search(
        self,
        term: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool = True,
        limit: int = 10,
    ) -> list[Product]:
        products = self.catalog.search_products(
            term=term,
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            limit=limit,
        )
        return [self._enrich(product) for product in products]

    def get(self, product_id: int | None = None, name: str | None = None) -> Product | None:
        product = self.catalog.get_product(product_id=product_id, name=name)
        return self._enrich(product) if product else None

    def promotion(self, product_id: int) -> Promotion | None:
        return self.promotions.active_promotion(product_id)

    def pix_price(self, product: Product) -> float | None:
        if product.has_active_promotion:
            return None
        return round(product.price_brl * 0.95, 2)

    def to_dict(self, product: Product) -> dict:
        return {
            "product_id": product.product_id,
            "nome": product.name,
            "categoria": product.category_name,
            "preco_tabela": product.price_brl,
            "preco_tabela_formatado": format_brl(product.price_brl),
            "promocao_ativa": product.has_active_promotion,
            "desconto_percentual": product.discount_percent,
            "preco_efetivo": product.effective_price,
            "preco_efetivo_formatado": format_brl(product.effective_price),
            "preco_pix": self.pix_price(product),
            "preco_pix_formatado": (
                format_brl(self.pix_price(product)) if self.pix_price(product) is not None else None
            ),
            "estoque": product.stock_quantity,
            "disponivel": product.available,
            "status": product.status,
            "descricao": product.description,
            "specs": product.specs,
        }
