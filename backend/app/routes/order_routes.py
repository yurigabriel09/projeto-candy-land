from app.controllers.order_controller import OrderController
from app.controllers.payment_controller import PaymentController
from app.utils.auth_decorator import token_required
from flask import Blueprint, g, jsonify, make_response, request

pedido_bp = Blueprint("order", __name__, url_prefix="/pedidos")

@pedido_bp.route("/webhooks/paypal", methods=["POST"])
def webhook_paypal():
    return PaymentController.webhook_paypal(request.headers, request.get_data(cache=True))

@pedido_bp.route("/<int:pedido_id>/pagamento/paypal-cancel", methods=["POST"])
@token_required
def cancelar_tentativa_paypal(pedido_id):
    return PaymentController.cancelar_tentativa_paypal(
        pedido_id, int(g.current_account_id), g.current_account_type, request.get_json(silent=True)
    )

@pedido_bp.route("/<int:pedido_id>/pagamento/paypal-capture", methods=["POST"])
@token_required
def capturar_pagamento_paypal(pedido_id):
    return PaymentController.capturar_paypal(
        pedido_id, int(g.current_account_id), g.current_account_type, request.get_json(silent=True)
    )


@pedido_bp.route("/webhooks/mercadopago", methods=["POST"])
def webhook_mercado_pago():
    # Checkout Pro também envia notificações merchant_order (ordem comercial).
    # Elas não são pagamentos e não podem aprovar pedido; apenas confirmamos o
    # recebimento para evitar retries/401 desnecessários. Eventos payment seguem
    # abaixo para validação criptográfica e consulta à API oficial.
    body = request.get_json(silent=True) or {}
    topic = str(request.args.get("topic") or "").strip().lower()
    query_type = str(request.args.get("type") or "").strip().lower()
    event_type = str(body.get("type") or body.get("topic") or query_type or "").strip().lower()
    action = str(body.get("action") or "").strip().lower()
    is_merchant_order = (
        topic in {"merchant_order", "merchant_orders", "order"}
        or event_type in {"merchant_order", "merchant_orders", "order"}
        or action.startswith("merchant_order.")
        or action.startswith("order.")
    )
    if is_merchant_order:
        return make_response(jsonify({"ok": True, "ignorado": True, "mensagem": "Notificação de ordem recebida; aguardando evento de pagamento."}), 200)

    # IPN/legacy callbacks (or callbacks without a verifiable JSON envelope) are
    # acknowledged only as a delivery receipt. They never mutate order/payment
    # state. The authenticated CheckoutResult -> GET /pagamento flow queries the
    # provider API and validates the amount/reference independently.
    if topic == "payment" and (
        not request.headers.get("x-signature")
        or not isinstance(body.get("data"), dict)
        or not body.get("data", {}).get("id")
    ):
        return make_response(jsonify({"ok": True, "ignorado": True, "mensagem": "Notificação legada recebida; o estado será reconciliado consultando a API de pagamentos."}), 200)

    query_data_id = request.args.get("data.id")
    if not query_data_id and topic == "payment":
        # Legacy notifications may include the payment ID in `id` instead of
        # `data.id`; it is only a consistency check after signature validation.
        query_data_id = request.args.get("id")
    return PaymentController.webhook_mercado_pago(
        request.headers,
        request.get_data(cache=True),
        query_data_id,
    )


@pedido_bp.route("", methods=["POST"])
@token_required
def criar_pedido():
    return OrderController.criar_pedido(
        request.get_json() or {}, int(g.current_account_id), g.current_account_type
    )


@pedido_bp.route("", methods=["GET"])
@token_required
def listar_pedidos():
    return OrderController.listar_pedidos(
        int(g.current_account_id), g.current_account_type
    )


@pedido_bp.route("/<int:pedido_id>", methods=["GET"])
@token_required
def buscar_pedido(pedido_id):
    return OrderController.buscar_pedido(
        pedido_id, int(g.current_account_id), g.current_account_type
    )


@pedido_bp.route("/<int:pedido_id>/status", methods=["PUT"])
@token_required
def atualizar_status(pedido_id):
    return OrderController.atualizar_status(
        pedido_id,
        request.get_json() or {},
        int(g.current_account_id),
        g.current_account_type,
    )


@pedido_bp.route("/<int:pedido_id>/entrega/status", methods=["PUT"])
@token_required
def atualizar_status_entrega(pedido_id):
    return OrderController.atualizar_status_entrega(
        pedido_id,
        request.get_json(silent=True) or {},
        int(g.current_account_id),
        g.current_account_type,
    )


@pedido_bp.route("/<int:pedido_id>/codigo-recebimento", methods=["POST"])
@token_required
def emitir_codigo_recebimento(pedido_id):
    return OrderController.emitir_codigo_recebimento(
        pedido_id, int(g.current_account_id), g.current_account_type
    )


@pedido_bp.route("/<int:pedido_id>/confirmar-recebimento", methods=["POST"])
@token_required
def confirmar_recebimento(pedido_id):
    return OrderController.confirmar_recebimento(
        pedido_id, request.get_json(silent=True) or {},
        int(g.current_account_id), g.current_account_type
    )


@pedido_bp.route("/<int:pedido_id>/cancelar", methods=["POST"])
@token_required
def cancelar_pedido(pedido_id):
    return OrderController.cancelar_pedido(
        pedido_id, int(g.current_account_id), g.current_account_type
    )


@pedido_bp.route("/<int:pedido_id>/pagamento", methods=["POST"])
@token_required
def criar_pagamento(pedido_id):
    return PaymentController.criar_pagamento(
        pedido_id,
        int(g.current_account_id),
        g.current_account_type,
        request.headers.get("Idempotency-Key"),
    )


@pedido_bp.route("/<int:pedido_id>/pagamento", methods=["GET"])
@token_required
def consultar_pagamento(pedido_id):
    return PaymentController.consultar_pagamento(
        pedido_id, int(g.current_account_id), g.current_account_type
    )


@pedido_bp.route("/<int:pedido_id>/pagamento/mock-result", methods=["POST"])
@token_required
def simular_resultado_pagamento(pedido_id):
    return PaymentController.simular_resultado(
        pedido_id,
        int(g.current_account_id),
        g.current_account_type,
        request.get_json(silent=True),
    )
