from flask import make_response, jsonify
from app.services.restaurant_service import RestauranteService

class RestaurantController:
    @staticmethod
    def listar_restaurantes():
        resultado = RestauranteService.listar_restaurantes()
        
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        
        return make_response(jsonify({
            "mensagem": resultado["mensagem"],
            "dados": resultado["dados"]
            }), 200)

    @staticmethod
    def buscar_restaurante(restaurant_id):
        resultado = RestauranteService.buscar_restaurante(restaurant_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 200)

    @staticmethod
    def criar_restaurante(dados):

        nome = dados.get("nome")
        email = dados.get(email)

        if not nome or not email:
            return make_response(jsonify({"erro": "O campo de nome e e-mail são obrigatórios."}), 400)
        
        resultado = RestauranteService.criar_restaurante(nome, email)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 201)

    @staticmethod
    def atualizar_restaurante(restaurant_id, dados):

        nome = dados.get("nome")
        email = dados.get("email")

        if not nome or not email:
            return make_response(jsonify({"erro": "O campo de nome e e-mail são obrigatórios."}), 400)
        
        resultado = RestauranteService.atualizar_restaurante(restaurant_id, nome, email)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 200)
    

    @staticmethod
    def deletar_restaurante(restaurant_id):
        resultado = RestauranteService.deletar_restaurante(restaurant_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        
        return make_response('', 204)