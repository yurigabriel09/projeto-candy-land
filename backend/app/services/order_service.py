import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4

from app.database.database import db
from app.models.address import Endereco
from app.models.delivery import EntregaPedido
from app.models.item_order import ItemPedido
from app.models.order import Pedido
from app.models.product import Produto
from app.models.restaurant import Restaurante
from app.services.order_workflow_service import (
    OrderTransitionError,
    validar_transicao_entrega,
    validar_transicao_pedido,
)
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

PAYMENT_METHODS = {"PIX", "CARTAO_CREDITO"}
ORDER_TYPES = {"DELIVERY", "PICKUP"}


class OrderService:
    @staticmethod
    def _money(value, field):
        try:
            result = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"{field} deve ser um valor monetário válido.")
        if not result.is_finite() or result < 0:
            raise ValueError(f"{field} não pode ser negativo nem inválido.")
        return result.quantize(Decimal("0.01"))

    @staticmethod
    def _validate_payment_method(method):
        if method not in PAYMENT_METHODS:
            raise ValueError("payment_method deve ser PIX ou CARTAO_CREDITO.")

    @staticmethod
    def _validate_order_type(order_type):
        if order_type not in ORDER_TYPES:
            raise ValueError("order_type deve ser DELIVERY ou PICKUP.")

    @staticmethod
    def _validate_address(user_id, address_id):
        address = Endereco.query.filter_by(
            id=address_id, id_usuario=user_id, ativo=True
        ).first()
        if not address:
            raise ValueError(
                "Endereço de entrega não pertence ao cliente ou está inativo."
            )
        return address

    @staticmethod
    def _resolve_pickup_address(restaurant_id):
        restaurant = Restaurante.query.filter_by(id=restaurant_id).first()
        if not restaurant:
            raise ValueError("Restaurante não encontrado.")

        address = None
        if restaurant.address_id:
            address = Endereco.query.filter_by(
                id=restaurant.address_id, ativo=True
            ).first()
            if address and address.id_restaurante not in (None, restaurant_id):
                address = None
        if not address:
            address = Endereco.query.filter_by(
                id_restaurante=restaurant_id, ativo=True
            ).first()
        if not address:
            raise ValueError(
                "O restaurante precisa ter um endereço ativo cadastrado para retirada."
            )
        return address

    @staticmethod
    def _validar_coordenada(valor, campo, minimo, maximo):
        try:
            coordenada = float(valor)
        except (TypeError, ValueError):
            raise ValueError(f"Informe {campo} válido no endereço cadastrado.")
        if not math.isfinite(coordenada) or not minimo <= coordenada <= maximo:
            raise ValueError(f"Informe {campo} válido no endereço cadastrado.")
        return coordenada

    @staticmethod
    def _resolver_endereco_restaurante(restaurant_id):
        restaurant = db.session.get(Restaurante, restaurant_id)
        if not restaurant:
            raise ValueError("Restaurante não encontrado.")

        address = None
        if restaurant.address_id:
            address = db.session.get(Endereco, restaurant.address_id)
            if address and (
                not address.ativo
                or address.id_restaurante not in (None, restaurant_id)
            ):
                address = None
        if not address:
            address = Endereco.query.filter_by(
                id_restaurante=restaurant_id, ativo=True
            ).first()
        if not address:
            raise ValueError(
                "Cadastre um endereço comercial ativo no restaurante para calcular a entrega."
            )
        return restaurant, address

    @staticmethod
    def _calcular_taxa_entrega(restaurant_id, customer_address):
        restaurant, restaurant_address = OrderService._resolver_endereco_restaurante(
            restaurant_id
        )
        if restaurant.raio_entrega_km is None:
            raise ValueError(
                "O restaurante precisa configurar o raio máximo de entrega em quilômetros."
            )

        try:
            radius_km = float(restaurant.raio_entrega_km)
        except (TypeError, ValueError):
            raise ValueError("O raio de entrega configurado é inválido.")
        if not math.isfinite(radius_km) or radius_km <= 0:
            raise ValueError("O raio de entrega deve ser maior que zero.")

        restaurant_lat = OrderService._validar_coordenada(
            restaurant_address.latitude, "latitude do restaurante", -90, 90
        )
        restaurant_lon = OrderService._validar_coordenada(
            restaurant_address.longitude, "longitude do restaurante", -180, 180
        )
        customer_lat = OrderService._validar_coordenada(
            customer_address.latitude, "latitude do endereço de entrega", -90, 90
        )
        customer_lon = OrderService._validar_coordenada(
            customer_address.longitude, "longitude do endereço de entrega", -180, 180
        )

        # Haversine: distância em linha reta sobre uma Terra aproximada como esfera.
        lat1, lat2 = math.radians(restaurant_lat), math.radians(customer_lat)
        delta_lat = lat2 - lat1
        delta_lon = math.radians(customer_lon - restaurant_lon)
        haversine = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        )
        haversine = min(1.0, max(0.0, haversine))
        distance_raw = 2 * 6371.0088 * math.asin(math.sqrt(haversine))
        if distance_raw > radius_km + 1e-9:
            distance_display = Decimal(str(distance_raw)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            raise ValueError(
                f"Endereço fora do raio de entrega. Distância estimada: {distance_display} km; "
                f"limite do restaurante: {Decimal(str(radius_km)).quantize(Decimal('0.01'))} km."
            )

        distance_km = Decimal(str(distance_raw)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        base_fee = OrderService._money(
            restaurant.taxa_entrega_base or 0, "taxa_entrega_base"
        )
        per_km_fee = OrderService._money(
            restaurant.taxa_entrega_por_km or 0, "taxa_entrega_por_km"
        )
        total_fee = (base_fee + distance_km * per_km_fee).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return total_fee, distance_km

    @staticmethod
    def _build_items(restaurant_id, items):
        if not isinstance(items, list) or not items:
            raise ValueError("O pedido deve possuir pelo menos um item.")

        snapshots = []
        subtotal = Decimal("0.00")

        for item in items:
            if not isinstance(item, dict):
                raise TypeError("Cada item do pedido deve ser um objeto.")

            product_id = item.get("produto_id")
            quantity = item.get("quantidade")

            if (
                isinstance(product_id, bool)
                or not isinstance(product_id, int)
                or isinstance(quantity, bool)
                or not isinstance(quantity, int)
            ):
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

            if isinstance(restaurant_id, bool) or not isinstance(restaurant_id, int):
                raise TypeError("restaurant_id é obrigatório e deve ser inteiro.")

            OrderService._validate_order_type(order_type)
            OrderService._validate_payment_method(payment_method)

            if order_type == "DELIVERY":
                if isinstance(address_id, bool) or not isinstance(address_id, int):
                    raise TypeError(
                        "delivery_address_id é obrigatório para entrega no endereço."
                    )
                customer_address = OrderService._validate_address(user_id, address_id)
                delivery_fee, delivery_distance_km = OrderService._calcular_taxa_entrega(
                    restaurant_id, customer_address
                )
            else:
                # A coluna legado delivery_address_id é obrigatória no banco. Para
                # retirada, ela referencia o endereço ativo do próprio restaurante.
                address_id = OrderService._resolve_pickup_address(restaurant_id).id

            snapshots, subtotal = OrderService._build_items(restaurant_id, items)
            # Ainda não existe motor server-side de promoções ou taxa da plataforma.
            # Não aceitar desconto/taxa enviados livremente pelo cliente.
            discount = Decimal("0.00")
            if order_type == "PICKUP":
                # Retirada nunca cobra taxa de entrega nem registra distância logística.
                delivery_fee = Decimal("0.00")
                delivery_distance_km = None
            # Para DELIVERY, delivery_fee é calculado exclusivamente pelo servidor.
            # O campo que eventualmente chegue no payload é ignorado.
            platform_fee = Decimal("0.00")
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
                delivery_distance_km=delivery_distance_km,
                platform_fee=platform_fee,
                total=total,
                order_type=order_type,
                status="PENDENTE_PAGAMENTO",
                payment_method=payment_method,
                general_note=dados.get("general_note"),
            )
            db.session.add(pedido)
            db.session.flush()
            if order_type == "DELIVERY":
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
    def _pagamento_ja_confirmado(status):
        return status in {
            "PAGAMENTO_CONFIRMADO",
            "RESTAURANTE_RECEBEU",
            "RESTAURANTE_ACEITOU",
            "PROCESSANDO",
            "PRONTO_PARA_ENTREGA",
            "ENTREGUE",
            "FINALIZADO",
        }

    @staticmethod
    def _resultado_confirmacao_repetida(pedido):
        if OrderService._pagamento_ja_confirmado(pedido.status):
            return {
                "success": True,
                "mensagem": (
                    "Pagamento já confirmado; nenhuma baixa duplicada de estoque foi aplicada."
                ),
                "dados": OrderService._to_dict(pedido),
            }
        if pedido.status == "CANCELADO":
            return {
                "success": False,
                "erro": "Não é possível confirmar pagamento de um pedido cancelado.",
                "status_code": 409,
            }
        return None

    @staticmethod
    def confirmar_pagamento(pedido_id):
        pedido = db.session.get(Pedido, pedido_id)
        if not pedido:
            return {
                "success": False,
                "erro": "Pedido não encontrado.",
                "status_code": 404,
            }

        if pedido.status != "PENDENTE_PAGAMENTO":
            repeticao = OrderService._resultado_confirmacao_repetida(pedido)
            if repeticao is not None:
                return repeticao
            return {
                "success": False,
                "erro": "O pedido não está pendente de pagamento.",
                "status_code": 409,
            }

        try:
            validar_transicao_pedido(pedido.status, "PAGAMENTO_CONFIRMADO")

            # A atualização condicional funciona como uma reivindicação atômica:
            # somente uma chamada pode mover o pedido de PENDENTE para CONFIRMADO.
            # Em concorrência, as demais chamadas veem rowcount=0 e não debitam estoque.
            reivindicacao = db.session.execute(
                update(Pedido)
                .where(
                    Pedido.id == pedido_id,
                    Pedido.status == "PENDENTE_PAGAMENTO",
                )
                .values(status="PAGAMENTO_CONFIRMADO")
                .execution_options(synchronize_session="fetch")
            )
            if reivindicacao.rowcount != 1:
                db.session.rollback()
                db.session.expire_all()
                pedido_atual = db.session.get(Pedido, pedido_id)
                if not pedido_atual:
                    return {
                        "success": False,
                        "erro": "Pedido não encontrado.",
                        "status_code": 404,
                    }
                repeticao = OrderService._resultado_confirmacao_repetida(pedido_atual)
                if repeticao is not None:
                    return repeticao
                return {
                    "success": False,
                    "erro": "O pedido foi alterado por outra operação; tente novamente.",
                    "status_code": 409,
                }

            itens = ItemPedido.query.filter_by(id_pedido=pedido_id).all()
            if not itens:
                db.session.rollback()
                return {
                    "success": False,
                    "erro": "Não é possível confirmar pagamento de um pedido sem itens.",
                    "status_code": 409,
                }

            # Agrupar linhas repetidas do mesmo produto evita validar/debitar
            # quantidades separadamente e mantém a operação toda-or-nada.
            quantidades = {}
            for item in itens:
                if item.quantidade <= 0:
                    db.session.rollback()
                    return {
                        "success": False,
                        "erro": f"Quantidade inválida no item do produto {item.id_produto}.",
                        "status_code": 409,
                    }
                quantidades[item.id_produto] = (
                    quantidades.get(item.id_produto, 0) + item.quantidade
                )

            for produto_id, quantidade in quantidades.items():
                produto_existente = db.session.get(Produto, produto_id)
                if not produto_existente:
                    db.session.rollback()
                    return {
                        "success": False,
                        "erro": f"Produto {produto_id} não encontrado para o pedido.",
                        "status_code": 409,
                    }

                baixa = db.session.execute(
                    update(Produto)
                    .where(
                        Produto.id == produto_id,
                        Produto.current_stock >= quantidade,
                    )
                    .values(current_stock=Produto.current_stock - quantidade)
                    .execution_options(synchronize_session=False)
                )
                if baixa.rowcount != 1:
                    db.session.rollback()
                    return {
                        "success": False,
                        "erro": f"Estoque insuficiente para o produto {produto_id}.",
                        "status_code": 409,
                    }

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
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao confirmar pagamento.",
                "status_code": 500,
            }

    @staticmethod
    def atualizar_status(pedido_id, novo_status, account_id, account_type):
        pedido = db.session.get(Pedido, pedido_id)
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
                "erro": (
                    "Esse status deve ser atualizado pelo sistema de pagamento "
                    "ou pela logística."
                ),
                "status_code": 403,
            }

        if novo_status == "CANCELADO":
            return OrderService._cancelar_pedido_transacional(
                pedido, mensagem_sucesso="Status atualizado com sucesso."
            )

        try:
            validar_transicao_pedido(pedido.status, novo_status)
            # Evita sobrescrever uma mudança simultânea de estado. Este UPDATE não
            # modifica estoque; os cancelamentos usam a transação dedicada abaixo.
            atualizacao = db.session.execute(
                update(Pedido)
                .where(Pedido.id == pedido_id, Pedido.status == pedido.status)
                .values(status=novo_status)
                .execution_options(synchronize_session="fetch")
            )
            if atualizacao.rowcount != 1:
                db.session.rollback()
                return {
                    "success": False,
                    "erro": "O pedido foi alterado por outra operação; tente novamente.",
                    "status_code": 409,
                }
            pedido.status = novo_status
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Status atualizado com sucesso.",
                "dados": OrderService._to_dict(pedido),
            }
        except OrderTransitionError as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 409}
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao atualizar o status do pedido.",
                "status_code": 500,
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

        return OrderService._cancelar_pedido_transacional(pedido)

    @staticmethod
    def _cancelar_pedido_transacional(
        pedido, mensagem_sucesso="Pedido cancelado com sucesso."
    ):
        status_anterior = pedido.status
        try:
            validar_transicao_pedido(status_anterior, "CANCELADO")
        except OrderTransitionError as exc:
            return {"success": False, "erro": str(exc), "status_code": 409}

        try:
            # Só uma requisição pode reivindicar a transição observada. A mudança
            # de estado, a reposição de estoque e o cancelamento logístico fazem
            # commit juntos; se qualquer parte falhar, tudo sofre rollback.
            cancelamento = db.session.execute(
                update(Pedido)
                .where(
                    Pedido.id == pedido.id,
                    Pedido.status == status_anterior,
                )
                .values(status="CANCELADO")
                .execution_options(synchronize_session="fetch")
            )
            if cancelamento.rowcount != 1:
                db.session.rollback()
                return {
                    "success": False,
                    "erro": "O pedido foi alterado por outra operação; atualize e tente novamente.",
                    "status_code": 409,
                }

            if status_anterior != "PENDENTE_PAGAMENTO":
                quantidades = {}
                for item in ItemPedido.query.filter_by(id_pedido=pedido.id).all():
                    if item.quantidade <= 0:
                        db.session.rollback()
                        return {
                            "success": False,
                            "erro": f"Quantidade inválida no item do produto {item.id_produto}.",
                            "status_code": 409,
                        }
                    quantidades[item.id_produto] = (
                        quantidades.get(item.id_produto, 0) + item.quantidade
                    )

                for produto_id, quantidade in quantidades.items():
                    reposicao = db.session.execute(
                        update(Produto)
                        .where(Produto.id == produto_id)
                        .values(current_stock=Produto.current_stock + quantidade)
                        .execution_options(synchronize_session=False)
                    )
                    if reposicao.rowcount != 1:
                        db.session.rollback()
                        return {
                            "success": False,
                            "erro": f"Não foi possível restaurar o estoque do produto {produto_id}.",
                            "status_code": 409,
                        }

            OrderService._cancelar_entrega(pedido.id)
            pedido.status = "CANCELADO"
            db.session.commit()
            return {
                "success": True,
                "mensagem": mensagem_sucesso,
                "dados": OrderService._to_dict(pedido),
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao cancelar o pedido e atualizar o estoque.",
                "status_code": 500,
            }

    @staticmethod
    def _cancelar_entrega(pedido_id):
        pedido = Pedido.query.filter_by(id=pedido_id).first()
        if pedido and pedido.order_type == "PICKUP":
            return
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido_id).first()
        if not entrega:
            entrega = EntregaPedido(pedido_id=pedido_id)
            db.session.add(entrega)
        entrega.status = "CANCELADO"
        entrega.cancelada_em = db.func.now()

    @staticmethod
    def atualizar_status_entrega(pedido_id, novo_status, account_id, account_type):
        pedido = Pedido.query.filter_by(id=pedido_id).first()
        if not pedido:
            return {
                "success": False,
                "erro": "Pedido não encontrado.",
                "status_code": 404,
            }

        # Até existir um papel próprio de entregador, somente o restaurante dono
        # do pedido pode atualizar o estado logístico. Não confiar apenas no token.
        if account_type != "BUSINESS" or pedido.restaurant_id != account_id:
            return {
                "success": False,
                "erro": "Apenas o restaurante responsável pode atualizar a entrega.",
                "status_code": 403,
            }

        if pedido.order_type == "PICKUP":
            return {
                "success": False,
                "erro": "Pedido para retirada não possui fluxo logístico de entrega.",
                "status_code": 409,
            }

        try:
            entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
            if not entrega:
                entrega = EntregaPedido(pedido_id=pedido.id)
                db.session.add(entrega)
                db.session.flush()

            validar_transicao_entrega(entrega.status, novo_status)
            if pedido.status == "CANCELADO" and novo_status != "CANCELADO":
                raise OrderTransitionError(
                    "Um pedido cancelado não pode retomar a entrega."
                )

            # A conclusão logística e a conclusão do pedido são uma única
            # transação. Não registrar entrega concluída se o pedido ainda não
            # puder transitar para ENTREGUE.
            if novo_status == "ENTREGA_CONCLUIDA" and pedido.status != "ENTREGUE":
                validar_transicao_pedido(pedido.status, "ENTREGUE")

            entrega.status = novo_status
            if novo_status == "PROCURANDO" and not entrega.iniciado_em:
                entrega.iniciado_em = db.func.now()
            elif novo_status == "ENTREGA_CONCLUIDA":
                entrega.concluida_em = db.func.now()
                pedido.delivered_at = db.func.now()
                pedido.status = "ENTREGUE"
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
            "delivery_address_id": (
                pedido.delivery_address_id if pedido.order_type == "DELIVERY" else None
            ),
            "pickup_address_id": (
                pedido.delivery_address_id if pedido.order_type == "PICKUP" else None
            ),
            "subtotal": float(pedido.subtotal),
            "discount": float(pedido.discount),
            "delivery_fee": float(pedido.delivery_fee),
            "delivery_distance_km": (
                float(pedido.delivery_distance_km)
                if pedido.delivery_distance_km is not None
                else None
            ),
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
