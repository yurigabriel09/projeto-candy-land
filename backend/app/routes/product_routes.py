from flask import Blueprint, request
from app.controllers.product_controller import ProductController

produto_bp = Blueprint(
    "product",
    __name__,
    url_prefix="/produtos"
)

@produto_bp.route("", methods=["GET"])
def listar_produtos():
    return ProductController.listar_produtos()

@produto_bp.route("/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    return ProductController.buscar_produto(produto_id)

@produto_bp.route("", methods=["POST"])
def criar_produto():
    dados = request.get_json() or {}
    return ProductController.criar_produto(dados)

@produto_bp.route("/<int:produto_id>", methods=["PUT"])
def atualizar_produto(produto_id):
    dados = request.get_json() or {}
    return ProductController.atualizar_produto(produto_id, dados)

@produto_bp.route("/<int:produto_id>", methods=["DELETE"])
def deletar_produto(produto_id):
    return ProductController.deletar_produto(produto_id)