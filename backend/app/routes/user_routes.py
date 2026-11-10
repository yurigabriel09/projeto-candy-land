from flask import Blueprint, jsonify, make_response, request

from app.controllers.user_controller import UserController
from app.utils.auth_decorator import account_owner_required, token_required

user_bp = Blueprint("user", __name__, url_prefix="/users")


@user_bp.route("", methods=["GET"])
@token_required
def listar_usuarios():
    return make_response(
        jsonify({"erro": "Consulta global de usuários não está disponível."}), 403
    )


@user_bp.route("/<int:user_id>", methods=["GET"])
@token_required
@account_owner_required("PERSONAL", "user_id")
def buscar_usuario(user_id):
    return UserController.buscar_usuario(user_id)


@user_bp.route("", methods=["POST"])
def criar_usuario():
    dados = request.get_json(silent=True) or {}
    return UserController.criar_usuario(dados)


@user_bp.route("/<int:user_id>/enderecos", methods=["GET", "POST"])
@token_required
@account_owner_required("PERSONAL", "user_id")
def gerenciar_enderecos_usuario(user_id):
    if request.method == "GET":
        return UserController.listar_enderecos(user_id)
    
    if request.method == "POST":
        dados = request.get_json(silent=True) or {}
        return UserController.cadastrar_endereco(user_id, dados)


@user_bp.route("/<int:user_id>/enderecos/<int:address_id>", methods=["PUT", "DELETE"])
@token_required
@account_owner_required("PERSONAL", "user_id")
def gerenciar_endereco_especifico(user_id, address_id):
    if request.method == "DELETE":
        return UserController.deletar_endereco(user_id, address_id)
    
    if request.method == "PUT":
        dados = request.get_json(silent=True) or {}
        dados["id"] = address_id
        return UserController.cadastrar_endereco(user_id, dados)


@user_bp.route("/<int:user_id>/enderecos/<int:address_id>/geocodificar", methods=["POST"])
@token_required
@account_owner_required("PERSONAL", "user_id")
def geocodificar_endereco_usuario(user_id, address_id):
    return UserController.geocodificar_endereco(user_id, address_id)


@user_bp.route("/<int:user_id>/enderecos/<int:address_id>/coordenadas", methods=["PUT"])
@token_required
@account_owner_required("PERSONAL", "user_id")
def atualizar_coordenadas_endereco(user_id, address_id):
    dados = request.get_json(silent=True) or {}
    return UserController.atualizar_coordenadas_endereco(user_id, address_id, dados)


@user_bp.route("/<int:user_id>", methods=["PUT"])
@token_required
@account_owner_required("PERSONAL", "user_id")
def atualizar_usuario(user_id):
    dados = request.get_json(silent=True) or {}
    return UserController.atualizar_usuario(user_id, dados)


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
@account_owner_required("PERSONAL", "user_id")
def deletar_usuario(user_id):
    return UserController.deletar_usuario(user_id)

@user_bp.route("/<int:user_id>/push-subscription", methods=["POST"])
@token_required
@account_owner_required("PERSONAL", "user_id")
def salvar_push_subscription(user_id):
    dados = request.get_json(silent=True) or {}
    return UserController.salvar_push_subscription(user_id, dados)