from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.domain.format import format_brl
from app.domain.models import ToolResult
from app.domain.services.catalog import CatalogService
from app.domain.services.conversations import ConversationService
from app.domain.services.orders import STATUS_LABELS, OrderService
from app.domain.services.policies import PolicyService
from app.domain.services.shipping import ShippingService
from app.logging import mask_email, mask_phone

logger = logging.getLogger(__name__)


class BuscarProdutosArgs(BaseModel):
    termo: str | None = None
    categoria: str | None = None
    preco_min: float | None = Field(default=None, ge=0)
    preco_max: float | None = Field(default=None, ge=0)
    apenas_em_estoque: bool = True
    limite: int = Field(default=10, ge=1, le=10)


class ObterProdutoArgs(BaseModel):
    produto_id: int | None = None
    nome: str | None = None


class ConsultarPromocaoArgs(BaseModel):
    produto_id: int


class IdentificarClienteArgs(BaseModel):
    nome: str = Field(min_length=2)
    contato: str = Field(min_length=3, description="Telefone ou e-mail do cliente")


class ListarPedidosArgs(BaseModel):
    customer_id: int


class ConsultarPedidoArgs(BaseModel):
    order_id: int
    customer_id: int


class ConsultarPoliticasArgs(BaseModel):
    pergunta: str = Field(min_length=2)


class InformacoesLojaArgs(BaseModel):
    pass


class CalcularFreteArgs(BaseModel):
    cidade: str = Field(min_length=2)
    subtotal: float = Field(ge=0)
    cep: str | None = None


class EscalarAtendimentoArgs(BaseModel):
    motivo: str = Field(min_length=2)
    resumo: str = Field(min_length=5)
    urgencia: Literal["baixa", "media", "alta"] = "media"


class ToolRegistry:
    def __init__(
        self,
        catalog: CatalogService,
        orders: OrderService,
        policies: PolicyService,
        shipping: ShippingService,
        conversations: ConversationService,
    ) -> None:
        self.catalog = catalog
        self.orders = orders
        self.policies = policies
        self.shipping = shipping
        self.conversations = conversations
        self._handlers = {
            "buscar_produtos": (BuscarProdutosArgs, self._buscar_produtos),
            "obter_produto": (ObterProdutoArgs, self._obter_produto),
            "consultar_promocao": (ConsultarPromocaoArgs, self._consultar_promocao),
            "identificar_cliente": (IdentificarClienteArgs, self._identificar_cliente),
            "listar_pedidos_cliente": (ListarPedidosArgs, self._listar_pedidos_cliente),
            "consultar_pedido": (ConsultarPedidoArgs, self._consultar_pedido),
            "consultar_politicas": (ConsultarPoliticasArgs, self._consultar_politicas),
            "informacoes_loja": (InformacoesLojaArgs, self._informacoes_loja),
            "calcular_frete": (CalcularFreteArgs, self._calcular_frete),
            "escalar_atendimento": (EscalarAtendimentoArgs, self._escalar_atendimento),
        }

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "buscar_produtos",
                    "description": (
                        "Busca instrumentos musicais no catálogo por termo, categoria e faixa de "
                        "preço. Use sempre que o cliente perguntar por modelos, preços ou "
                        "disponibilidade. Retorna até 10 produtos."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "termo": {
                                "type": "string",
                                "description": "Marca, modelo ou palavra-chave.",
                            },
                            "categoria": {
                                "type": "string",
                                "description": "Categoria do instrumento.",
                            },
                            "preco_min": {
                                "type": "number",
                                "description": "Preço mínimo em reais.",
                            },
                            "preco_max": {
                                "type": "number",
                                "description": "Preço máximo em reais.",
                            },
                            "apenas_em_estoque": {
                                "type": "boolean",
                                "default": True,
                                "description": "Se verdadeiro, retorna apenas produtos disponíveis.",
                            },
                            "limite": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 10,
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "obter_produto",
                    "description": (
                        "Retorna a ficha completa de um produto por ID ou nome, incluindo "
                        "especificações, estoque, preço e promoção ativa."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "produto_id": {"type": "integer"},
                            "nome": {"type": "string"},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "consultar_promocao",
                    "description": "Consulta a promoção ativa de um produto e o preço com PIX.",
                    "parameters": {
                        "type": "object",
                        "properties": {"produto_id": {"type": "integer"}},
                        "required": ["produto_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "identificar_cliente",
                    "description": (
                        "Identifica o cliente por nome completo e telefone ou e-mail. Use antes "
                        "de listar ou consultar pedidos. Retorna o customer_id ou ambiguidade."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string"},
                            "contato": {"type": "string", "description": "Telefone ou e-mail."},
                        },
                        "required": ["nome", "contato"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_pedidos_cliente",
                    "description": "Lista os pedidos do cliente previamente identificado.",
                    "parameters": {
                        "type": "object",
                        "properties": {"customer_id": {"type": "integer"}},
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "consultar_pedido",
                    "description": (
                        "Consulta um pedido do cliente identificado, com status, itens, rastreio, "
                        "previsão e prazos de devolução/garantia."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "integer"},
                            "customer_id": {"type": "integer"},
                        },
                        "required": ["order_id", "customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "consultar_politicas",
                    "description": (
                        "Recupera trechos do manual de políticas sobre horário, endereço, trocas, "
                        "devoluções, garantia, pagamento, promoções e frete. Sempre cite a seção."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {"pergunta": {"type": "string"}},
                        "required": ["pergunta"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "informacoes_loja",
                    "description": "Retorna endereço, telefone, WhatsApp, e-mail e horários da loja.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calcular_frete",
                    "description": (
                        "Calcula a regra de frete para Campo Grande e região metropolitana. Fora "
                        "da região, informa que o valor é sob cotação."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cidade": {"type": "string"},
                            "subtotal": {"type": "number"},
                            "cep": {"type": "string"},
                        },
                        "required": ["cidade", "subtotal"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "escalar_atendimento",
                    "description": (
                        "Registra um escalonamento para atendimento humano com motivo, resumo e "
                        "urgência. Use em reclamações, casos sensíveis ou pedido explícito."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "motivo": {"type": "string"},
                            "resumo": {"type": "string"},
                            "urgencia": {
                                "type": "string",
                                "enum": ["baixa", "media", "alta"],
                                "default": "media",
                            },
                        },
                        "required": ["motivo", "resumo"],
                    },
                },
            },
        ]

    def execute(self, name: str, arguments: dict[str, Any], session_id: str) -> ToolResult:
        entry = self._handlers.get(name)
        if entry is None:
            return ToolResult(
                name=name,
                arguments=arguments,
                result={"erro": f"Ferramenta desconhecida: {name}"},
                ok=False,
                error="unknown_tool",
            )
        arg_model, handler = entry
        try:
            parsed = arg_model(**arguments)
            result = handler(parsed, session_id)
            return ToolResult(name=name, arguments=arguments, result=result, ok=True)
        except ValidationError as exc:
            logger.warning("Argumentos inválidos para %s: %s", name, exc)
            return ToolResult(
                name=name,
                arguments=arguments,
                result={"erro": "Argumentos inválidos.", "detalhes": exc.errors()},
                ok=False,
                error="validation_error",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Falha ao executar ferramenta %s", name)
            return ToolResult(
                name=name,
                arguments=arguments,
                result={"erro": "Não foi possível concluir a consulta."},
                ok=False,
                error=str(exc),
            )

    # Handlers -----------------------------------------------------------------
    def _buscar_produtos(self, args: BuscarProdutosArgs, _: str) -> dict:
        products = self.catalog.search(
            term=args.termo,
            category=args.categoria,
            min_price=args.preco_min,
            max_price=args.preco_max,
            in_stock=args.apenas_em_estoque,
            limit=args.limite,
        )
        items = [self.catalog.to_dict(product) for product in products]
        message = (
            "Nenhum produto encontrado com esses filtros. Tente ampliar a faixa de preço ou "
            "buscar outra categoria."
            if not items
            else f"Encontrei {len(items)} produto(s)."
        )
        return {"produtos": items, "quantidade": len(items), "mensagem": message}

    def _obter_produto(self, args: ObterProdutoArgs, _: str) -> dict:
        product = self.catalog.get(product_id=args.produto_id, name=args.nome)
        if product is None:
            return {"erro": "Produto não encontrado."}
        return {"produto": self.catalog.to_dict(product)}

    def _consultar_promocao(self, args: ConsultarPromocaoArgs, _: str) -> dict:
        product = self.catalog.get(product_id=args.produto_id)
        if product is None:
            return {"erro": "Produto não encontrado."}
        promo = self.catalog.promotion(args.produto_id)
        data = self.catalog.to_dict(product)
        if promo is None:
            data["mensagem"] = "Não há promoção ativa para este produto."
        else:
            data["promocao"] = {
                "promotion_id": promo.promotion_id,
                "descricao": promo.description,
                "desconto_percentual": promo.discount_percent,
                "preco_promocional": product.effective_price,
                "preco_promocional_formatado": format_brl(product.effective_price),
            }
        return data

    def _identificar_cliente(self, args: IdentificarClienteArgs, _: str) -> dict:
        matches = self.orders.identify(args.nome, args.contato)
        if not matches:
            return {
                "status": "nao_encontrado",
                "mensagem": (
                    "Não encontrei um cadastro com esse nome e contato. Confira o nome completo "
                    "e o telefone ou e-mail usado na compra."
                ),
            }
        customers = [
            {
                "customer_id": customer.customer_id,
                "nome": customer.name,
                "telefone": mask_phone(customer.phone),
                "email": mask_email(customer.email),
                "cidade": customer.city,
            }
            for customer in matches
        ]
        if len(customers) > 1:
            return {
                "status": "ambiguo",
                "clientes": customers,
                "mensagem": "Encontrei mais de um cadastro. Peça um dado adicional para desambiguar.",
            }
        return {"status": "ok", "cliente": customers[0]}

    def _listar_pedidos_cliente(self, args: ListarPedidosArgs, _: str) -> dict:
        customer = self.orders.get_customer(args.customer_id)
        if customer is None:
            return {"erro": "Cliente não encontrado."}
        orders = self.orders.list_orders(args.customer_id)
        return {
            "cliente": self.orders.customer_to_dict(customer),
            "pedidos": [
                {
                    "order_id": order.order_id,
                    "data_pedido": order.order_date.isoformat(),
                    "status": order.status,
                    "status_label": STATUS_LABELS.get(order.status, order.status),
                    "total_brl": order.total_brl,
                    "total_formatado": format_brl(order.total_brl),
                    "rastreio": order.tracking_code,
                }
                for order in orders
            ],
        }

    def _consultar_pedido(self, args: ConsultarPedidoArgs, _: str) -> dict:
        details = self.orders.order_details(args.order_id, args.customer_id)
        if details is None:
            return {
                "status": "nao_encontrado",
                "mensagem": (
                    "Não encontrei esse pedido vinculado ao cliente identificado. Confira o "
                    "número do pedido e os dados de identificação."
                ),
            }
        details["citacoes"] = [
            {"section": "4.1", "page": 4, "source": "Manual de Políticas"},
            {"section": "4.2", "page": 4, "source": "Manual de Políticas"},
            {"section": "8.1", "page": 7, "source": "Manual de Políticas"},
        ]
        return {"status": "ok", **details}

    def _consultar_politicas(self, args: ConsultarPoliticasArgs, _: str) -> dict:
        chunks = self.policies.search(args.pergunta)
        citations = self.policies.citations(chunks)
        if not chunks:
            return {
                "trechos": [],
                "citacoes": [],
                "mensagem": (
                    "Não encontrei uma regra específica para essa dúvida. Ofereça escalonamento "
                    "para a equipe."
                ),
            }
        return {
            "trechos": self.policies.chunks_to_dict(chunks),
            "citacoes": [citation.model_dump() for citation in citations],
        }

    def _informacoes_loja(self, _: InformacoesLojaArgs, __: str) -> dict:
        data = self.policies.store_info_to_dict()
        data["citacoes"] = [
            {"section": "1.2", "page": 2, "source": "Manual de Políticas"},
            {"section": "2", "page": 2, "source": "Manual de Políticas"},
            {"section": "7", "page": 6, "source": "Manual de Políticas"},
        ]
        return data

    def _calcular_frete(self, args: CalcularFreteArgs, _: str) -> dict:
        quote = self.shipping.quote(args.cidade, args.subtotal, args.cep)
        data = quote.model_dump()
        data["subtotal_formatado"] = format_brl(args.subtotal)
        if quote.amount_brl is not None:
            data["valor_formatado"] = format_brl(quote.amount_brl)
        return data

    def _escalar_atendimento(self, args: EscalarAtendimentoArgs, session_id: str) -> dict:
        handoff = self.conversations.record_handoff(
            session_id=session_id,
            reason=args.motivo,
            summary=args.resumo,
        )
        return {
            "protocolo": handoff.id,
            "status": handoff.status,
            "urgencia": args.urgencia,
            "mensagem": (
                "Encaminhei seu atendimento para a equipe. O retorno ocorre em até 24 horas úteis."
            ),
        }
