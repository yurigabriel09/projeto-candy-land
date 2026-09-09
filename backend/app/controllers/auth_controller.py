from flask import make_response, jsonify
from app.services.auth_service import AuthService


class AuthController:

    @staticmethod
    def enviar_codigo_telefone(dados):
        telefone = dados.get("telefone")

        if not telefone:
            return make_response(jsonify({"erro": "Campo 'telefone' é obrigatório."}), 400)

        resultado = AuthService.enviar_codigo_telefone(telefone)

        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])

        return make_response(jsonify({"mensagem": resultado["mensagem"]}), 200)


    @staticmethod
    def enviar_codigo_email(dados):
        email = dados.get("email")

        if not email:
            return make_response(jsonify({"erro": "Campo 'email' é obrigatório."}), 400)

        resultado = AuthService.enviar_codigo_email(email)

        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])

        return make_response(jsonify({"mensagem": resultado["mensagem"]}), 200)


    @staticmethod
    def verificar_codigo(dados):
        tipo = dados.get("tipo")
        valor = dados.get("valor")
        codigo = dados.get("codigo")

        if not tipo or not valor or not codigo:
            return make_response(jsonify({"erro": "Campos 'tipo', 'valor' e 'codigo' são obrigatórios."}), 400)

        resultado = AuthService.verificar_codigo(tipo, valor, codigo)

        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])

        status_http = 201 if resultado["criado"] else 200

        return make_response(jsonify({
            "mensagem": resultado["mensagem"],
            "usuario": resultado["dados"]
        }), status_http)


    @staticmethod
    def enviar_codigo_whatsapp(dados):
        telefone = dados.get("telefone")

        if not telefone:
            return make_response(jsonify({"erro": "Campo 'telefone' é obrigatório."}), 400)

        resultado = AuthService.enviar_codigo_whatsapp(telefone)

        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])

        return make_response(jsonify({"mensagem": resultado["mensagem"]}), 200)


    @staticmethod
    def verificar_codigo_whatsapp(dados):
        telefone = dados.get("telefone")
        codigo = dados.get("codigo")

        if not telefone or not codigo:
            return make_response(jsonify({"erro": "Campos 'telefone' e 'codigo' são obrigatórios."}), 400)

        resultado = AuthService.verificar_codigo_whatsapp(telefone, codigo)

        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])

        status_http = 201 if resultado["criado"] else 200

        return make_response(jsonify({
            "mensagem": resultado["mensagem"],
            "usuario": resultado["dados"]
        }), status_http)