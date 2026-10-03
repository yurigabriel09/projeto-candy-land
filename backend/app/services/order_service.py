from decimal import Decimal, InvalidOperation
from uuid import uuid4

from app.database.database import db
from app.models.address import Endereco
from app.models.delivery import EntregaPedido
from app.models.item_order import ItemPedido
from app.models.order import Pedido
from app.models.product import Produto
from app.services.order_workflow_service import (
    OrderTransitionError,
    validar_transicao_entrega,
    validar_transicao_pedido,
)
from sqlalchemy.exc import SQLAlchemyError

PAYMENT_METHODS = {"PIX", "CARTAO_CREDITO"}
ORDER_TYPES = {"DELIVERY"}


class OrderService:
    @staticmethod
    def _money(value, field):
        try:
            result = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"{field} deve ser um valor monetário válido.")
        if result < 0:
            raise ValueError(f"{field} não pode ser negativo.")
        return result.quantize(Decimal("0.01"))

    @staticmethod
    def _validate_payment_method(method):
        if method not in PAYMENT_METHODS:
            raise ValueError("payment_method deve ser PIX ou CARTAO_CREDITO.")

    @staticmethod
    def _validate_order_type(order_type):
        if order_type not in ORDER_TYPES:
            raise ValueError("order_type deve ser DELIVERY.")

    @staticmethod
    def _validate_address(user_id, address_id):
        address = Endereco.query.filter_by(id=address_id, id_usuario=user_id).first()
        if not address:
            raise ValueError("Endereço de entrega não pertence ao cliente.")
        return address

    @staticmethod
    def _build_items(restaurant_id, items):
        if not isinstance(items, list) or not items:
            raise ValueError("O pedido deve possuir pelo menos um item.")

        snapshots = []
        subtotal = Decimal("0.00")

        for item in items:
            product_id = item.get("produto_id")
            quantity = item.get("quantidade")

            if not isinstance(product_id, int) or not isinstance(quantity, int):
                raise TypeError("produto_id e quantidade devem ser inteiros.")
            if quantity <= 0:
                raise ValueError("A quantidade deve ser maior que zero.")

            product = Produto.query.filter_by(id=product_id).first()
            if not product:
                raise ValueError(f"Produto {product_id} não encontrado.")
            if product.restaurant_id != restaurant_id:
                raise ValueError(
                    f"Produto {product_id} não pertence ao restaurante do pedido."
                )
            if not product.is_available:
                raise ValueError(f"Produto {product_id} não está disponível.")
            if product.current_stock < quantity:
                raise ValueError(f"Estoque insuficiente para o produto {product_id}.")

            unit_price = Decimal(str(product.price)).quantize(Decimal("0.01"))
            subtotal += unit_price * quantity
            snapshots.append((product, item, unit_price, quantity))

        return snapshots, subtotal.quantize(Decimal("0.01"))

    @staticmethod
    def criar_pedido(user_id, dados):
        try:
            restaurant_id = dados.get("restaurant_id")
            order_type = dados.get("order_type", "DELIVERY")
            payment_method = dados.get("payment_method")
            items = dados.get("items")
            address_id = dados.get("delivery_address_id")

            if not isinstance(restaurant_id, int):
                raise TypeError("restaurant_id é obrigatório e deve ser inteiro.")

            OrderService._validate_order_type(order_type)
            OrderService._validate_payment_method(payment_method)

            if not isinstance(address_id, int):
                raise TypeError("delivery_address_id é obrigatório para o pedido.")
            OrderService._validate_address(user_id, address_id)

            snapshots, subtotal = OrderService._build_items(restaurant_id, items)
            discount = OrderService._money(dados.get("discount", 0), "discount")
            delivery_fee = OrderService._money(
                dados.get("delivery_fee", 0), "delivery_fee"
            )
            platform_fee = OrderService._money(
                dados.get("platform_fee", 0), "platform_fee"
            )
            total = subtotal - discount + delivery_fee + platform_fee

            if total < 0:
                raise ValueError("O total do pedido não pode ser negativo.")

            pedido = Pedido(
                order_code=f"CL-{uuid4().hex[:10].upper()}",
                user_id=user_id,
                restaurant_id=restaurant_id,
                delivery_address_id=address_id,
                subtotal=subtotal,
                discount=discount,
                delivery_fee=delivery_fee,
                platform_fee=platform_fee,
                total=total,
                order_type=order_type,
                status="PENDENTE_PAGAMENTO",
                payment_method=payment_method,
                general_note=dados.get("general_note"),
            )
            db.session.add(pedido)
            db.session.flush()
            db.session.add(EntregaPedido(pedido_id=pedido.id))

            for product, item, unit_price, quantity in snapshots:
                db.session.add(
                    ItemPedido(
                        id_pedido=pedido.id,
                        id_produto=product.id,
                        quantidade=quantity,
                        preco_unitario=unit_price,
                        observacoes=item.get("observacoes"),
                        detalhes_personalizacao=item.get("detalhes_personalizacao"),
                    )
                )

            db.session.commit()
            return {
                "success": True,
                "mensagem": "Pedido criado com sucesso!",
                "dados": OrderService._to_dict(pedido),
            }
        except (TypeError, ValueError, SQLAlchemyError) as exc:
            db.session.rollback()
            if isinstance(exc, (TypeError, ValueError)):
                return {"success": False, "erro": str(exc), "status_code": 400}
            return {
                "success": False,
                "erro": "Falha ao criar pedido.",
                "status_code": 500,
            }

    @staticmethod
    def listar_pedidos(account_id, account_type):
        try:
            if account_type == "PERSONAL":
                pedidos = (
                    Pedido.query.filter_by(user_id=account_id)
                    .order_by(Pedido.created_at.desc())
                    .all()
                )
            elif account_type == "BUSINESS":
                pedidos = (
                    Pedido.query.filter_by(restaurant_id=account_id)
                    .order_by(Pedido.created_at.desc())
                    .all()
                )
            else:
                return {
                    "success": False,
                    "erro": "Tipo de conta não autorizado.",
                    "status_code": 403,
                }

            return {
                "success": True,
                "mensagem": "Pedidos consultados.",
                "dados": [OrderService._to_dict(p) for p in pedidos],
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao consultar pedidos.",
                "status_code": 500,
            }

    @staticmethod
    def buscar_pedido(pedido_id, account_id, account_type):
        pedido = Pedido.query.filter_by(id=pedido_id).first()
        if not pedido:
            return {
                "success": False,
                "erro": "Pedido não encontrado.",
                "status_code": 404,
            }

        if (account_type == "PERSONAL" and pedido.user_id != account_id) or (
            account_type == "BUSINESS" and pedido.restaurant_id != account_id
        ):
            return {
                "success": False,
                "erro": "Você não tem acesso a este pedido.",
                "status_code": 403,
            }

        return {
            "success": True,
            "mensagem": "Pedido encontrado.",
            "dados": OrderService._to_dict(pedido),
        }

    @staticmethod
    def confirmar_pagamento(pedido_id):
        pedido = Pedido.query.filter_by(id=pedido_id).first()
        if not pedido:
            return {
                "success": False,
                "erro": "Pedido não encontrado.",
                "status_code": 404,
            }

        try:
            validar_transicao_pedido(pedido.status, "PAGAMENTO_CONFIRMADO")

            itens = ItemPedido.query.filter_by(id_pedido=pedido.id).all()
            produtos = []
            for item in itens:
                product = Produto.query.filter_by(id=item.id_produto).first()
                if not product:
                    raise ValueError(
                        f"Produto {item.id_produto} não encontrado para o pedido."
                    )
                if product.current_stock < item.quantidade:
                    return {
                        "success": False,
                        "erro": f"Estoque insuficiente para o produto {product.id}.",
                        "status_code": 409,
                    }
                produtos.append((product, item.quantidade))

            for product, quantity in produtos:
                product.current_stock -= quantity

            pedido.status = "PAGAMENTO_CONFIRMADO"
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Pagamento confirmado e estoque atualizado.",
                "dados": OrderService._to_dict(pedido),
            }
        except OrderTransitionError as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 409}
        except (ValueError, SQLAlchemyError) as exc:
            db.session.rollback()
            if isinstance(exc, ValueError):
                return {"success": False, "erro": str(exc), "status_code": 400}
            return {
                "success": False,
                "erro": "Falha ao confirmar pagamento.",
                "status_code": 500,
            }

    @staticmethod
    def atualizar_status(pedido_id, novo_status, account_id, account_type):
        pedido = Pedido.query.filter_by(id=pedido_id).first()
        if not pedido:
            return {
                "success": False,
                "erro": "Pedido não encontrado.",
                "status_code": 404,
            }

        if account_type != "BUSINESS" or pedido.restaurant_id != account_id:
            return {
                "success": False,
                "erro": "Apenas o restaurante responsável pode atualizar o status.",
                "status_code": 403,
            }

        status_permitidos_restaurante = {
            "RESTAURANTE_RECEBEU",
            "RESTAURANTE_ACEITOU",
            "PROCESSANDO",
            "PRONTO_PARA_ENTREGA",
            "CANCELADO",
        }
        if novo_status not in status_permitidos_restaurante:
            return {
                "success": False,
                "erro": "Esse status deve ser atualizado pelo sistema de pagamento ou pela logística.",
                "status_code": 403,
            }

        try:
            validar_transicao_pedido(pedido.status, novo_status)
        except OrderTransitionError as exc:
            return {"success": False, "erro": str(exc), "status_code": 409}

        if novo_status == "CANCELADO" and pedido.status != "PENDENTE_PAGAMENTO":
            for item in ItemPedido.query.filter_by(id_pedido=pedido.id).all():
                product = Produto.query.filter_by(id=item.id_produto).first()
                if product:
                    product.current_stock += item.quantidade
            OrderService._cancelar_entrega(pedido.id)

        pedido.status = novo_status
        db.session.commit()
        return {
            "success": True,
            "mensagem": "Status atualizado com sucesso.",
            "dados": OrderService._to_dict(pedido),
        }

    @staticmethod
    def cancelar_pedido(pedido_id, user_id):
        pedido = Pedido.query.filter_by(id=pedido_id, user_id=user_id).first()
        if not pedido:
            return {
                "success": False,
                "erro": "Pedido não encontrado.",
                "status_code": 404,
            }

        try:
            validar_transicao_pedido(pedido.status, "CANCELADO")
        except OrderTransitionError as exc:
            return {"success": False, "erro": str(exc), "status_code": 409}

        if pedido.status != "PENDENTE_PAGAMENTO":
            for item in ItemPedido.query.filter_by(id_pedido=pedido.id).all():
                product = Produto.query.filter_by(id=item.id_produto).first()
                if product:
                    product.current_stock += item.quantidade
            OrderService._cancelar_entrega(pedido.id)

        pedido.status = "CANCELADO"
        db.session.commit()
        return {"success": True, "mensagem": "Pedido cancelado com sucesso."}

    @staticmethod
    def _cancelar_entrega(pedido_id):
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido_id).first()
        if not entrega:
            entrega = EntregaPedido(pedido_id=pedido_id)
            db.session.add(entrega)
        entrega.status = "CANCELADO"
        entrega.cancelada_em = db.func.now()

    @staticmethod
    def atualizar_status_entrega(pedido_id, novo_status):
        pedido = Pedido.query.filter_by(id=pedido_id).first()
        if not pedido:
            return {
                "success": False,
                "erro": "Pedido não encontrado.",
                "status_code": 404,
            }

        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
        if not entrega:
            entrega = EntregaPedido(pedido_id=pedido.id)
            db.session.add(entrega)
            db.session.flush()

        try:
            validar_transicao_entrega(entrega.status, novo_status)
            if pedido.status == "CANCELADO" and novo_status != "CANCELADO":
                raise OrderTransitionError(
                    "Um pedido cancelado não pode retomar a entrega."
                )

            entrega.status = novo_status
            if novo_status == "PROCURANDO" and not entrega.iniciado_em:
                entrega.iniciado_em = db.func.now()
            elif novo_status == "ENTREGA_CONCLUIDA":
                entrega.concluida_em = db.func.now()
                pedido.delivered_at = db.func.now()
            elif novo_status == "CANCELADO":
                entrega.cancelada_em = db.func.now()

            db.session.commit()
            return {
                "success": True,
                "mensagem": "Status da entrega atualizado com sucesso.",
                "dados": OrderService._to_dict(pedido),
            }
        except OrderTransitionError as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 409}
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao atualizar a entrega.",
                "status_code": 500,
            }

    @staticmethod
    def _to_dict(pedido):
        return {
            "id": pedido.id,
            "order_code": pedido.order_code,
            "user_id": pedido.user_id,
            "restaurant_id": pedido.restaurant_id,
            "delivery_address_id": pedido.delivery_address_id,
            "subtotal": float(pedido.subtotal),
            "discount": float(pedido.discount),
            "delivery_fee": float(pedido.delivery_fee),
            "platform_fee": float(pedido.platform_fee),
            "total": float(pedido.total),
            "order_type": pedido.order_type,
            "status": pedido.status,
            "payment_method": pedido.payment_method,
            "general_note": pedido.general_note,
            "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
            "estimated_delivery_at": pedido.estimated_delivery_at.isoformat()
            if pedido.estimated_delivery_at
            else None,
            "delivered_at": pedido.delivered_at.isoformat()
            if pedido.delivered_at
            else None,
            "entrega": (
                {
                    "id": pedido.entrega.id,
                    "status": pedido.entrega.status,
                    "iniciado_em": pedido.entrega.iniciado_em.isoformat()
                    if pedido.entrega.iniciado_em
                    else None,
                    "concluida_em": pedido.entrega.concluida_em.isoformat()
                    if pedido.entrega.concluida_em
                    else None,
                    "cancelada_em": pedido.entrega.cancelada_em.isoformat()
                    if pedido.entrega.cancelada_em
                    else None,
                }
                if pedido.entrega
                else None
            ),
            "items": [
                {
                    "id": item.id,
                    "produto_id": item.id_produto,
                    "quantidade": item.quantidade,
                    "preco_unitario": float(item.preco_unitario),
                    "observacoes": item.observacoes,
                    "detalhes_personalizacao": item.detalhes_personalizacao,
                }
                for item in ItemPedido.query.filter_by(id_pedido=pedido.id).all()
            ],
        }
