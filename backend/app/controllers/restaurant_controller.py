from flask import make_response, jsonify
from app.services.restaurant_service import RestauranteService

class RestaurantController:
    @staticmethod
    def listar_restaurantes():
        resultado = RestauranteService.listar_restaurantes()
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 200)

    @staticmethod
    def buscar_restaurante(restaurant_id):
        resultado = RestauranteService.buscar_restaurante(restaurant_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 200)

    @staticmethod
    def criar_restaurante(dados):
        resultado = RestauranteService.criar_restaurante(
            cnpj=dados.get("cnpj"),
            razao_social=dados.get("razao_social"),
            nome=dados.get("nome"),
            email=dados.get("email"),
            telefone=dados.get("telefone"),
            cpf_responsavel=dados.get("cpf_responsavel"),
            endereco=dados.get("endereco")
    )   
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])

        return make_response(jsonify({
            "mensagem": resultado["mensagem"],
            "dados": resultado["dados"]
        }), 201)

    @staticmethod
    def atualizar_restaurante(restaurant_id, dados):
        resultado = RestauranteService.atualizar_restaurante(restaurant_id, nome=dados.get("nome"), email=dados.get("email"))
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 200)
    

    @staticmethod
    def deletar_restaurante(restaurant_id):
        resultado = RestauranteService.deletar_restaurante(restaurant_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        
        return make_response('', 204)