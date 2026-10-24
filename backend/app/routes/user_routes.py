from flask import Blueprint, jsonify, make_response, request

from app.controllers.user_controller import UserController
from app.utils.auth_decorator import account_owner_required, token_required

user_bp = Blueprint("user", __name__, url_prefix="/users")


@user_bp.route("", methods=["GET"])
@token_required
def listar_usuarios():
    # Ainda não existe papel ADMIN na plataforma. Não liberar leitura global de PII.
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
    # O serviço exige tentativa_id com e-mail e telefone já verificados.
    dados = request.get_json(silent=True) or {}
    return UserController.criar_usuario(dados)


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
