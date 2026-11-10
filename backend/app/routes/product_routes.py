from app.controllers.product_controller import ProductController
from app.utils.auth_decorator import token_required
from flask import Blueprint, g, request

produto_bp = Blueprint("product", __name__, url_prefix="/produtos")


@produto_bp.route("", methods=["GET"])
def listar_produtos():
    return ProductController.listar_produtos()


@produto_bp.route("/<int:produto_id>", methods=["GET"])
@token_required
def buscar_produto(produto_id):
    return ProductController.buscar_produto(
        produto_id, int(g.current_account_id), g.current_account_type
    )


@produto_bp.route("", methods=["POST"])
@token_required
def criar_produto():
    dados = request.get_json() or {}
    return ProductController.criar_produto(
        dados, int(g.current_account_id), g.current_account_type
    )


@produto_bp.route("/<int:produto_id>", methods=["PUT"])
@token_required
def atualizar_produto(produto_id):
    dados = request.get_json() or {}
    return ProductController.atualizar_produto(
        produto_id, dados, int(g.current_account_id), g.current_account_type
    )


@produto_bp.route("/<int:produto_id>", methods=["DELETE"])
@token_required
def deletar_produto(produto_id):
    return ProductController.deletar_produto(
        produto_id, int(g.current_account_id), g.current_account_type
    )

@produto_bp.route("/<int:produto_id>/imagem", methods=["POST"])
@token_required
def enviar_imagem_produto(produto_id):
    arquivo = request.files.get("imagem")
    return ProductController.enviar_imagem(
        produto_id, arquivo, int(g.current_account_id), g.current_account_type
    )