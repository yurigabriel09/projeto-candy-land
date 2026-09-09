from flask import make_response, jsonify
from app.services.product_service import ProductService


class ProductController:
    @staticmethod
    def listar_produtos():

        produtos = ProductService.listar_produtos()

        if not produtos["success"]:
            return make_response(jsonify({"erro": produtos["erro"]}), produtos["status_code"])
        
        return make_response(jsonify({
            "mensagem": produtos["mensagem"],
            "produtos": produtos["dados"]
        }), 200)


    @staticmethod
    def buscar_produto(produto_id):

        produto = ProductService.buscar_produto(produto_id)

        if not produto["success"]:
            return make_response(jsonify({"erro": produto["erro"]}), produto["status_code"])

        return make_response(jsonify({
            "mensagem": produto["mensagem"],
            "produto": produto["dados"]
        }), 200)


    @staticmethod
    def criar_produto(dados):

        restaurant_id = dados.get("restaurante_id")
        category_id = dados.get("categoria_id")
        name = dados.get("nome")
        description = dados.get("descricao", "")
        price = dados.get("preco")
        is_available = dados.get("disponivel", True)
        is_imported = dados.get("importado", False)
        current_stock = dados.get("qtd_estoque", 0)
        allows_customization = dados.get("permite_customizacao", False)

        campos_obrigatorios = {
            "restaurante_id": restaurant_id,
            "categoria_id": category_id,
            "nome": name,
            "preco": price,
        }

        faltando = [campo for campo, valor in campos_obrigatorios.items() if valor is None or valor == ""]

        if faltando:
            return make_response(jsonify({
                "erro": f"Campos obrigatórios ausentes: {', '.join(faltando)}"
            }), 400)
        
        if price < 0 or current_stock < 0:
            return make_response(jsonify({
                "erro": "Preço ou Quantidade em Estoque não podem ser menores que 0."
            }), 400)

            
        produto = ProductService.criar_produto(dados)

        if not produto["success"]:
            return make_response(jsonify({"erro": produto["erro"]}), produto["status_code"])

        return make_response(jsonify({
            "mensagem": produto["mensagem"],
            "produto": produto["dados"],
        }), 201)


    @staticmethod
    def atualizar_produto(produto_id, dados):

        if "preco" in dados and dados.get("preco") is not None and dados.get("preco") < 0:
            return make_response(jsonify({
                "erro": "Preço não pode ser menor que 0."
            }), 400)

        if "qtd_estoque" in dados and dados.get("qtd_estoque") is not None and dados.get("qtd_estoque") < 0:
            return make_response(jsonify({
                "erro": "Quantidade em estoque não pode ser menor que 0."
            }), 400)

        produto = ProductService.atualizar_produto(produto_id, dados)

        if not produto["success"]:
            return make_response(jsonify({"erro": produto["erro"]}), produto["status_code"])

        return make_response(jsonify({
            "mensagem": produto["mensagem"],
            "produto": produto["dados"]
        }), 200)


    @staticmethod
    def deletar_produto(produto_id):

        resultado = ProductService.deletar_produto(produto_id)

        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])

        return make_response('', 204)