from flask import Blueprint, request
from app.controllers.restaurant_controller import RestaurantController

restaurante_bp = Blueprint(
    "restaurant",
    __name__,
    url_prefix="/restaurantes"
)

@restaurante_bp.route("", methods=["GET"])
def listar_usuarios():
    return RestaurantController.listar_restaurantes()

@restaurante_bp.route("/<int:restaurante_id>", methods=["GET"])
def buscar_usuario(restaurante_id):
    return RestaurantController.buscar_restaurante(restaurante_id)

@restaurante_bp.route("", methods=["POST"])
def criar_usuario():
    dados = request.get_json() or {}
    return RestaurantController.criar_restaurante(dados)

@restaurante_bp.route("/<int:restaurante_id>", methods=["PUT"])
def atualizar_usuario(restaurante_id):
    dados = request.get_json() or {}
    return RestaurantController.atualizar_restaurante(restaurante_id, dados)

@restaurante_bp.route("/<int:restaurante_id>", methods=["DELETE"])
def deletar_usuario(restaurante_id):
    return RestaurantController.deletar_restaurante(restaurante_id)