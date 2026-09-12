from flask import jsonify, make_response
from app.services.auth_service import AuthService

class AuthController:
    @staticmethod
    def solicitar_codigo(dados):
        canal = dados.get("canal", "")
        valor = dados.get("valor", "")

        if not canal or not valor:
            return make_response(
                jsonify({"erro": "Canal e valor são obrigatórios."}),
                400
            )

        resultado = AuthService.iniciar_autenticacao(canal, valor)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(jsonify(resultado), 200)

    @staticmethod
    def solicitar_segundo_codigo(dados):
        tentativa_id = dados.get("tentativa_id", "")
        valor = dados.get("valor", "")

        if not tentativa_id or not valor:
            return make_response(
                jsonify({"erro": "Tentativa e valor são obrigatórios."}),
                400
            )

        resultado = AuthService.solicitar_segundo_codigo(
            tentativa_id,
            valor
        )

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(jsonify(resultado), 200)

    @staticmethod
    def verificar_codigo(dados):
        tentativa_id = dados.get("tentativa_id", "")
        codigo = dados.get("codigo", "").strip()

        if not tentativa_id or not codigo:
            return make_response(
                jsonify({"erro": "Tentativa e código são obrigatórios."}),
                400
            )

        resultado = AuthService.verificar_codigo(
            tentativa_id,
            codigo
        )

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(jsonify(resultado), 200)