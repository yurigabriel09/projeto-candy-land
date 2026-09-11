from flask import make_response, jsonify
from app.services.product_service import ProductService

class ProductController:
    @staticmethod
    def listar_produtos():
        resultado = ProductService.listar_produtos()

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(
            jsonify({
                "mensagem": resultado["mensagem"],
                "produtos": resultado["dados"]
            }),
            200
        )

    @staticmethod
    def buscar_produto(produto_id):
        resultado = ProductService.buscar_produto(produto_id)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(
            jsonify({
                "mensagem": resultado["mensagem"],
                "produto": resultado["dados"]
            }),
            200
        )

    @staticmethod
    def criar_produto(dados):
        restaurant_id = dados.get("restaurante_id")
        category_id = dados.get("categoria_id")
        name = dados.get("nome")
        price = dados.get("preco")
        stock = dados.get("qtd_estoque", 0)

        campos_obrigatorios = {
            "restaurante_id": restaurant_id,
            "categoria_id": category_id,
            "nome": name,
            "preco": price
        }

        faltando = [
            campo
            for campo, valor in campos_obrigatorios.items()
            if valor is None or valor == ""
        ]

        if faltando:
            return make_response(
                jsonify({
                    "erro": f"Campos obrigatórios ausentes: {', '.join(faltando)}"
                }),
                400
            )

        if not isinstance(name, str) or not name.strip():
            return make_response(
                jsonify({"erro": "Nome do produto é obrigatório."}),
                400
            )

        if not isinstance(price, (int, float)) or isinstance(price, bool):
            return make_response(
                jsonify({"erro": "Preço deve ser um número."}),
                400
            )

        if price <= 0:
            return make_response(
                jsonify({"erro": "Preço deve ser maior que zero."}),
                400
            )

        if not isinstance(stock, int) or isinstance(stock, bool):
            return make_response(
                jsonify({"erro": "Quantidade em estoque deve ser um número inteiro."}),
                400
            )

        if stock < 0:
            return make_response(
                jsonify({"erro": "Quantidade em estoque não pode ser menor que 0."}),
                400
            )

        if "disponivel" in dados and not isinstance(dados["disponivel"], bool):
            return make_response(
                jsonify({"erro": "O campo disponivel deve ser booleano."}),
                400
            )

        if "importado" in dados and not isinstance(dados["importado"], bool):
            return make_response(
                jsonify({"erro": "O campo importado deve ser booleano."}),
                400
            )

        if "permite_customizacao" in dados and not isinstance(
            dados["permite_customizacao"],
            bool
        ):
            return make_response(
                jsonify({
                    "erro": "O campo permite_customizacao deve ser booleano."
                }),
                400
            )

        resultado = ProductService.criar_produto(dados)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(
            jsonify({
                "mensagem": resultado["mensagem"],
                "produto": resultado["dados"]
            }),
            201
        )

    @staticmethod
    def atualizar_produto(produto_id, dados):
        if not dados:
            return make_response(
                jsonify({"erro": "Nenhum dado informado para atualização."}),
                400
            )

        if "nome" in dados:
            if not isinstance(dados["nome"], str) or not dados["nome"].strip():
                return make_response(
                    jsonify({"erro": "Nome do produto não pode ser vazio."}),
                    400
                )

        if "preco" in dados:
            preco = dados["preco"]

            if not isinstance(preco, (int, float)) or isinstance(preco, bool):
                return make_response(
                    jsonify({"erro": "Preço deve ser um número."}),
                    400
                )

            if preco <= 0:
                return make_response(
                    jsonify({"erro": "Preço deve ser maior que zero."}),
                    400
                )

        if "qtd_estoque" in dados:
            estoque = dados["qtd_estoque"]

            if not isinstance(estoque, int) or isinstance(estoque, bool):
                return make_response(
                    jsonify({
                        "erro": "Quantidade em estoque deve ser um número inteiro."
                    }),
                    400
                )

            if estoque < 0:
                return make_response(
                    jsonify({
                        "erro": "Quantidade em estoque não pode ser menor que 0."
                    }),
                    400
                )

        campos_booleanos = [
            "disponivel",
            "importado",
            "permite_customizacao"
        ]

        for campo in campos_booleanos:
            if campo in dados and not isinstance(dados[campo], bool):
                return make_response(
                    jsonify({
                        "erro": f"O campo {campo} deve ser booleano."
                    }),
                    400
                )

        resultado = ProductService.atualizar_produto(
            produto_id,
            dados
        )

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(
            jsonify({
                "mensagem": resultado["mensagem"],
                "produto": resultado["dados"]
            }),
            200
        )

    @staticmethod
    def deletar_produto(produto_id):
        resultado = ProductService.deletar_produto(produto_id)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response("", 204)