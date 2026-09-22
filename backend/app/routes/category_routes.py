from flask import Blueprint, request, g
from app.controllers.category_controller import CategoryController
from app.utils.auth_decorator import token_required

categoria_bp = Blueprint("category", __name__, url_prefix="/categorias")

@categoria_bp.route("", methods=["GET"])
@token_required
def listar_categorias():
    return CategoryController.listar_categorias(int(g.current_account_id))

@categoria_bp.route("/<int:categoria_id>", methods=["GET"])
@token_required
def buscar_categoria(categoria_id):
    return CategoryController.buscar_categoria(categoria_id, int(g.current_account_id))

@categoria_bp.route("", methods=["POST"])
@token_required
def criar_categoria():
    dados = request.get_json() or {}
    return CategoryController.criar_categoria(dados, int(g.current_account_id), g.current_account_type)

@categoria_bp.route("/<int:categoria_id>", methods=["PUT"])
@token_required
def atualizar_categoria(categoria_id):
    dados = request.get_json() or {}
    return CategoryController.atualizar_categoria(categoria_id, dados, int(g.current_account_id), g.current_account_type)

@categoria_bp.route("/<int:categoria_id>", methods=["DELETE"])
@token_required
def deletar_categoria(categoria_id):
    return CategoryController.deletar_categoria(categoria_id, int(g.current_account_id), g.current_account_type)