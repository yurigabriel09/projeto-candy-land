from flask import make_response, jsonify
from app.services.user_service import UserService

class UserController:
    @staticmethod
    def listar_usuarios():
        resultado = UserService.listar_usuarios()
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 200)

    @staticmethod
    def buscar_usuario(user_id):
        resultado = UserService.buscar_usuario(user_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 200)

    @staticmethod
    def criar_usuario(dados):
        resultado = UserService.criar_usuario(
            nome_completo=dados.get("nome_completo"),
            email=dados.get("email"),
            telefone=dados.get("telefone"),
            cpf=dados.get("cpf"),
            data_nascimento=dados.get("data_nascimento"),
            endereco=dados.get("endereco")
        )
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 201)

    @staticmethod
    def atualizar_usuario(user_id, dados):
        resultado = UserService.atualizar_usuario(
            user_id,
            nome_completo=dados.get("nome_completo"),
            email=dados.get("email"),
            telefone=dados.get("telefone"),
            data_nascimento=dados.get("data_nascimento")
        )
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "dados": resultado["dados"]}), 200)

    @staticmethod
    def deletar_usuario(user_id):
        resultado = UserService.deletar_usuario(user_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"]}), 204)