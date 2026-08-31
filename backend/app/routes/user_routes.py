from flask import Blueprint, request
from app.controllers.user_controller import UserController

user_bp = Blueprint(
    "user",
    __name__,
    url_prefix="/users"
)

@user_bp.route("", methods=["GET"])
def listar_usuarios():
    return UserController.listar_usuarios()

@user_bp.route("/<int:user_id>", methods=["GET"])
def buscar_usuario(user_id):
    return UserController.buscar_usuario(user_id)

@user_bp.route("", methods=["POST"])
def criar_usuario():
    dados = request.get_json() or {}
    return UserController.criar_usuario(dados)

@user_bp.route("/<int:user_id>", methods=["PUT"])
def atualizar_usuario(user_id):
    dados = request.get_json() or {}
    return UserController.atualizar_usuario(user_id, dados)

@user_bp.route("/<int:user_id>", methods=["DELETE"])
def deletar_usuario(user_id):
    return UserController.deletar_usuario(user_id)