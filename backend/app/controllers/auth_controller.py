from flask import jsonify, make_response

from app.services.auth_service import AuthService

class AuthController:
    @staticmethod
    def solicitar_codigo(dados):
        tipo = dados.get("tipo", "EMAIL").upper()

        if tipo == "WHATSAPP":
            destino = dados.get("telefone", "").strip()
        else:
            destino = dados.get("email", "").strip().lower()

        if not destino:
            campo = "Telefone" if tipo == "WHATSAPP" else "E-mail"
            return make_response(jsonify({"erro": f"{campo} é obrigatório."}), 400)

        resultado = AuthService.solicitar_codigo(destino, tipo=tipo)

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
        tipo = dados.get("tipo", "EMAIL").upper()
        codigo = dados.get("codigo", "").strip()

        if tipo == "WHATSAPP":
            destino = dados.get("telefone", "").strip()
        else:
            destino = dados.get("email", "").strip().lower()

        if not destino or not codigo:
            campo = "Telefone" if tipo == "WHATSAPP" else "E-mail"
            return make_response(
                jsonify({"erro": f"{campo} e código são obrigatórios."}),
                400
            )

        resultado = AuthService.verificar_codigo(destino, codigo, tipo=tipo)

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