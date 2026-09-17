from flask import jsonify, make_response
from app.services.auth_service import AuthService
from app.services.facebook_auth_service import FacebookAuthService


class AuthController:
    @staticmethod
    def solicitar_codigo(dados):
        canal = dados.get("canal", "")
        valor = dados.get("valor", "")

        if not canal or not valor:
            return make_response(
                jsonify({"erro": "Canal e valor são obrigatórios."}), 400
            )

        resultado = AuthService.iniciar_autenticacao(canal, valor)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}), resultado["status_code"]
            )

        return make_response(jsonify(resultado), 200)

    @staticmethod
    def solicitar_segundo_codigo(dados):
        tentativa_id = dados.get("tentativa_id", "")
        valor = dados.get("valor", "")

        if not tentativa_id or not valor:
            return make_response(
                jsonify({"erro": "Tentativa e valor são obrigatórios."}), 400
            )

        resultado = AuthService.solicitar_segundo_codigo(tentativa_id, valor)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}), resultado["status_code"]
            )

        return make_response(jsonify(resultado), 200)

    @staticmethod
    def verificar_codigo(dados):
        tentativa_id = dados.get("tentativa_id", "")
        codigo = dados.get("codigo", "").strip()

        if not tentativa_id or not codigo:
            return make_response(
                jsonify({"erro": "Tentativa e código são obrigatórios."}), 400
            )

        resultado = AuthService.verificar_codigo(tentativa_id, codigo)

        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}), resultado["status_code"]
            )

        return make_response(jsonify(resultado), 200)

    @staticmethod
    def autenticar_google(dados):
        credential = dados.get("credential", "")
        telefone = dados.get("telefone")

        if not credential:
            return make_response(
                jsonify({"erro": "Credencial do Google é obrigatória."}), 400
            )

        resultado = AuthService.autenticar_google(credential, telefone)

        # Não é erro: o Google já foi validado e agora precisamos do celular.
        if resultado.get("precisa_telefone"):
            return make_response(jsonify(resultado), 200)

        if not resultado["success"]:
            return make_response(
                jsonify(
                    {
                        "erro": resultado["erro"],
                        "precisa_telefone": resultado.get("precisa_telefone", False),
                        "email": resultado.get("email"),
                    }
                ),
                resultado["status_code"],
            )

        return make_response(jsonify(resultado), 200)

    @staticmethod
    def completar_facebook(dados):
        ticket = dados.get("ticket", "")
        telefone = dados.get("telefone")

        if not ticket:
            return make_response(
                jsonify({"erro": "Ticket do Facebook é obrigatório."}),
                400,
            )

        try:
            dados_facebook = FacebookAuthService.validar_ticket(ticket)
        except ValueError as erro:
            return make_response(jsonify({"erro": str(erro)}), 401)

        resultado = AuthService.autenticar_facebook(dados_facebook, telefone)

        if resultado.get("precisa_telefone"):
            return make_response(jsonify(resultado), 200)

        if not resultado["success"]:
            return make_response(
                jsonify(resultado),
                resultado["status_code"],
            )

        return make_response(jsonify(resultado), 200)
