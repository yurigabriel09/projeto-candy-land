from flask import jsonify, make_response

from app.services.auth_service import AuthService

class AuthController:
    @staticmethod
    def solicitar_codigo(dados):
        email = dados.get("email", "").strip().lower()

        if not email:
            return make_response(jsonify({"erro": "E-mail é obrigatório."}), 400)

        resultado = AuthService.solicitar_codigo(email)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(
            jsonify({"mensagem": resultado["mensagem"]}),
            200
        )

    @staticmethod
    def verificar_codigo(dados):
        email = dados.get("email", "").strip().lower()
        codigo = dados.get("codigo", "").strip()

        if not email or not codigo:
            return make_response(
                jsonify({"erro": "E-mail e código são obrigatórios."}),
                400
            )

        resultado = AuthService.verificar_codigo(email, codigo)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}),
                resultado["status_code"]
            )

        return make_response(
            jsonify({
                "mensagem": resultado["mensagem"],
                "dados": resultado["dados"]
            }),
            200
        )