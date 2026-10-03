from flask import Blueprint, g, request

from app.controllers.order_controller import OrderController
from app.utils.auth_decorator import token_required

pedido_bp = Blueprint("order", __name__, url_prefix="/pedidos")


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


@pedido_bp.route("/<int:pedido_id>/cancelar", methods=["POST"])
@token_required
def cancelar_pedido(pedido_id):
    return OrderController.cancelar_pedido(
        pedido_id, int(g.current_account_id), g.current_account_type
    )
