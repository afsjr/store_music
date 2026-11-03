from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from app.domain.format import format_brl
from app.domain.models import ToolResult
from app.domain.services.catalog import CatalogService
from app.domain.services.conversations import ConversationService
from app.domain.services.orders import STATUS_LABELS, OrderService
from app.domain.services.payments import PaymentService
from app.domain.services.policies import PolicyService
from app.domain.services.shipping import ShippingService
from app.domain.services.store_hours import StoreHoursService
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


class SimularPagamentoArgs(BaseModel):
    produto_id: int | None = None
    nome: str | None = None
    forma: Literal["pix", "debito", "credito", "boleto"]
    parcelas: int = Field(default=1, ge=1, le=12)

    @model_validator(mode="after")
    def _require_product(self) -> SimularPagamentoArgs:
        if self.produto_id is None and not self.nome:
            raise ValueError("Informe produto_id ou nome do produto.")
        return self


class BuscarAlternativasArgs(BaseModel):
    produto_id: int | None = None
    nome: str | None = None
    limite: int = Field(default=3, ge=1, le=5)

    @model_validator(mode="after")
    def _require_product(self) -> BuscarAlternativasArgs:
        if self.produto_id is None and not self.nome:
            raise ValueError("Informe produto_id ou nome do produto.")
        return self


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


class StatusLojaArgs(BaseModel):
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
        self.payments = PaymentService()
        self.hours = StoreHoursService()
        self._handlers = {
            "buscar_produtos": (BuscarProdutosArgs, self._buscar_produtos),
            "obter_produto": (ObterProdutoArgs, self._obter_produto),
            "consultar_promocao": (ConsultarPromocaoArgs, self._consultar_promocao),
            "simular_pagamento": (SimularPagamentoArgs, self._simular_pagamento),
            "buscar_alternativas": (BuscarAlternativasArgs, self._buscar_alternativas),
            "identificar_cliente": (IdentificarClienteArgs, self._identificar_cliente),
            "listar_pedidos_cliente": (ListarPedidosArgs, self._listar_pedidos_cliente),
            "consultar_pedido": (ConsultarPedidoArgs, self._consultar_pedido),
            "consultar_politicas": (ConsultarPoliticasArgs, self._consultar_politicas),
            "informacoes_loja": (InformacoesLojaArgs, self._informacoes_loja),
            "status_loja": (StatusLojaArgs, self._status_loja),
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
                    "description": (
                        "Consulta a promoção ativa de um produto e o preço com PIX. Se não houver "
                        "promoção ativa, retorna a última promoção expirada e o preço atual."
                    ),
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
                    "name": "simular_pagamento",
                    "description": (
                        "Calcula de forma determinística o valor no PIX, débito, crédito parcelado "
                        "ou boleto. Use para qualquer pergunta de pagamento, desconto de PIX ou "
                        "parcelamento. Informe produto_id ou nome e forma de pagamento."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "produto_id": {"type": "integer"},
                            "nome": {"type": "string"},
                            "forma": {
                                "type": "string",
                                "enum": ["pix", "debito", "credito", "boleto"],
                            },
                            "parcelas": {
                                "type": "integer",
                                "default": 1,
                                "minimum": 1,
                                "maximum": 12,
                            },
                        },
                        "required": ["forma"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "buscar_alternativas",
                    "description": (
                        "Busca até 5 produtos semelhantes disponíveis na mesma categoria, "
                        "ordenados por proximidade de preço. Use quando o produto estiver "
                        "esgotado, descontinuado ou ainda não disponível."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "produto_id": {"type": "integer"},
                            "nome": {"type": "string"},
                            "limite": {
                                "type": "integer",
                                "default": 3,
                                "minimum": 1,
                                "maximum": 5,
                            },
                        },
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
                    "name": "status_loja",
                    "description": (
                        "Informa se a loja está aberta agora, o horário de hoje e o próximo "
                        "horário de atendimento. Use quando o cliente perguntar se está aberto "
                        "ou quando o atendimento ocorrer fora do expediente."
                    ),
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
        unavailable_mode = False
        if not products and args.apenas_em_estoque and args.termo:
            products = self.catalog.search(
                term=args.termo,
                category=args.categoria,
                min_price=args.preco_min,
                max_price=args.preco_max,
                in_stock=False,
                limit=args.limite,
            )
            unavailable_mode = bool(products)

        items = [self.catalog.to_dict(product) for product in products]
        payload: dict = {"produtos": items, "quantidade": len(items)}
        if unavailable_mode and products:
            alternatives = self.catalog.alternatives(products[0].product_id, limit=3)
            payload["alternativas"] = [self.catalog.to_dict(item) for item in alternatives]
            payload["mensagem"] = (
                "Nenhum produto disponível com esses filtros. Encontrei modelo(s) fora de "
                "estoque ou descontinuado(s) e separei até 3 alternativas disponíveis. "
                "Apresente as alternativas ao cliente."
            )
        elif not items:
            payload["mensagem"] = (
                "Nenhum produto encontrado com esses filtros. Tente ampliar a faixa de preço "
                "ou buscar outra categoria."
            )
        else:
            payload["mensagem"] = f"Encontrei {len(items)} produto(s)."
        return payload

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
        if promo is not None:
            data["promocao"] = {
                "promotion_id": promo.promotion_id,
                "descricao": promo.description,
                "desconto_percentual": promo.discount_percent,
                "preco_original": product.price_brl,
                "preco_original_formatado": format_brl(product.price_brl),
                "preco_promocional": product.effective_price,
                "preco_promocional_formatado": format_brl(product.effective_price),
            }
            data["mensagem"] = (
                "Promoção ativa. Apresente preço original, percentual de desconto e preço "
                "final. Promoções não são cumulativas com o desconto de PIX."
            )
            return data

        expired = self.catalog.expired_promotion(args.produto_id)
        if expired is not None:
            data["promocao_expirada"] = {
                "promotion_id": expired.promotion_id,
                "descricao": expired.description,
                "desconto_percentual": expired.discount_percent,
                "preco_original": product.price_brl,
                "preco_original_formatado": format_brl(product.price_brl),
            }
            data["preco_atual"] = product.price_brl
            data["preco_atual_formatado"] = format_brl(product.price_brl)
            data["mensagem"] = (
                f"A promoção de {expired.discount_percent:.0f}% expirou. "
                f"O preço atual é {format_brl(product.price_brl)}. "
                "Não há rain check nem promessa de desconto retroativo."
            )
            return data

        data["mensagem"] = "Não há promoção ativa nem promoção expirada para este produto."
        return data

    def _simular_pagamento(self, args: SimularPagamentoArgs, _: str) -> dict:
        product = self.catalog.get(product_id=args.produto_id, name=args.nome)
        if product is None:
            return {"erro": "Produto não encontrado."}
        simulation = self.payments.simulate(product, args.forma, args.parcelas)
        data = simulation.model_dump()
        data["preco_tabela_formatado"] = format_brl(simulation.preco_tabela)
        data["preco_base_formatado"] = format_brl(simulation.preco_base)
        data["preco_final_formatado"] = format_brl(simulation.preco_final)
        data["total_formatado"] = format_brl(simulation.total)
        if simulation.valor_parcela is not None:
            data["valor_parcela_formatado"] = format_brl(simulation.valor_parcela)
        return data

    def _buscar_alternativas(self, args: BuscarAlternativasArgs, _: str) -> dict:
        product = self.catalog.get(product_id=args.produto_id, name=args.nome)
        if product is None:
            return {"erro": "Produto não encontrado."}
        alternatives = self.catalog.alternatives(product.product_id, args.limite)
        if not product.available and alternatives:
            message = (
                "O produto está indisponível. Encontrei estas alternativas disponíveis na "
                "mesma categoria."
            )
        elif not product.available:
            message = (
                "O produto está indisponível e não encontrei alternativas disponíveis na "
                "mesma categoria."
            )
        else:
            message = "O produto está disponível. Estas são opções semelhantes do catálogo."
        return {
            "produto": self.catalog.to_dict(product),
            "alternativas": [self.catalog.to_dict(item) for item in alternatives],
            "quantidade": len(alternatives),
            "mensagem": message,
        }

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
        status = self.hours.status()
        data["status_agora"] = {
            "aberto": status.aberto,
            "mensagem": status.mensagem,
            "proxima_abertura": (
                status.proxima_abertura.strftime("%d/%m/%Y %H:%M")
                if status.proxima_abertura
                else None
            ),
        }
        data["citacoes"] = [
            {"section": "1.2", "page": 2, "source": "Manual de Políticas"},
            {"section": "2", "page": 2, "source": "Manual de Políticas"},
            {"section": "7", "page": 6, "source": "Manual de Políticas"},
        ]
        return data

    def _status_loja(self, _: StatusLojaArgs, __: str) -> dict:
        status = self.hours.status()
        data = status.model_dump()
        data["agora"] = status.agora.strftime("%d/%m/%Y %H:%M")
        data["proxima_abertura"] = (
            status.proxima_abertura.strftime("%d/%m/%Y %H:%M") if status.proxima_abertura else None
        )
        data["horarios"] = self.policies.store_info().hours
        data["citacoes"] = [
            {"section": "2", "page": 2, "source": "Manual de Políticas"},
            {"section": "7.1", "page": 6, "source": "Manual de Políticas"},
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
