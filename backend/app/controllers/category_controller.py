from flask import make_response, jsonify
from app.services.category_service import CategoryService

class CategoryController:
    @staticmethod
    def listar_categorias(restaurant_id):
        resultado = CategoryService.listar_categorias(restaurant_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "categorias": resultado["dados"]}), 200)

    @staticmethod
    def buscar_categoria(categoria_id, restaurant_id):
        resultado = CategoryService.buscar_categoria(categoria_id, restaurant_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "categoria": resultado["dados"]}), 200)

    TIPOS_VALIDOS = {"Bolos", "Chocolates", "Pirulitos", "Cupcakes", "Pudins", "Balas", "Donuts", "Cookies"}

    @staticmethod
    def criar_categoria(dados, restaurant_id, tipo_conta):
        if tipo_conta != "BUSINESS":
            return make_response(jsonify({"erro": "Apenas contas de restaurante podem cadastrar categorias."}), 403)

        nome = dados.get("nome")
        if not nome or nome not in CategoryController.TIPOS_VALIDOS:
            return make_response(jsonify({"erro": f"Categoria inválida. Escolha entre: {', '.join(CategoryController.TIPOS_VALIDOS)}"}), 400)

        resultado = CategoryService.criar_categoria(restaurant_id, dados)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "categoria": resultado["dados"]}), 201)
    @staticmethod
    def atualizar_categoria(categoria_id, dados, restaurant_id, tipo_conta):
        if tipo_conta != "BUSINESS":
            return make_response(jsonify({"erro": "Apenas contas de restaurante podem atualizar categorias."}), 403)

        if not dados:
            return make_response(jsonify({"erro": "Nenhum dado informado para atualização."}), 400)

        if "nome" in dados and (not isinstance(dados["nome"], str) or not dados["nome"].strip()):
            return make_response(jsonify({"erro": "Nome da categoria não pode ser vazio."}), 400)

        resultado = CategoryService.atualizar_categoria(categoria_id, restaurant_id, dados)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "categoria": resultado["dados"]}), 200)

    @staticmethod
    def deletar_categoria(categoria_id, restaurant_id, tipo_conta):
        if tipo_conta != "BUSINESS":
            return make_response(jsonify({"erro": "Apenas contas de restaurante podem remover categorias."}), 403)
        resultado = CategoryService.deletar_categoria(categoria_id, restaurant_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response("", 204)