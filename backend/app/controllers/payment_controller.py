from flask import jsonify, make_response

from app.services.payment_service import PaymentService


class PaymentController:
    @staticmethod
    def criar_pagamento(pedido_id, account_id, account_type, idempotency_key=None):
        resultado = PaymentService.criar_pagamento(
            pedido_id, account_id, account_type, idempotency_key
        )
        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}), resultado["status_code"]
            )
        status_code = 201 if resultado.get("created") else 200
        return make_response(
            jsonify(
                {
                    "mensagem": resultado["mensagem"],
                    "pagamento": resultado["dados"],
                }
            ),
            status_code,
        )

    @staticmethod
    def consultar_pagamento(pedido_id, account_id, account_type):
        resultado = PaymentService.consultar_pagamento(
            pedido_id, account_id, account_type
        )
        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}), resultado["status_code"]
            )
        return make_response(
            jsonify(
                {
                    "mensagem": resultado["mensagem"],
                    "pagamento": resultado["dados"],
                }
            ),
            200,
        )

    @staticmethod
    def simular_resultado(pedido_id, account_id, account_type, dados):
        if not isinstance(dados, dict):
            return make_response(
                jsonify({"erro": "O corpo da requisição deve ser um objeto JSON."}),
                400,
            )
        resultado = PaymentService.simular_resultado(
            pedido_id, account_id, account_type, dados.get("outcome")
        )
        if not resultado["success"]:
            body = {"erro": resultado["erro"]}
            if resultado.get("dados"):
                body["pagamento"] = resultado["dados"]
            return make_response(jsonify(body), resultado["status_code"])
        body = {"mensagem": resultado["mensagem"]}
        if resultado.get("dados"):
            body["pagamento"] = resultado["dados"]
        if resultado.get("pedido"):
            body["pedido"] = resultado["pedido"]
        return make_response(jsonify(body), 200)
    @staticmethod
    def cancelar_tentativa_paypal(pedido_id, account_id, account_type, dados):
        if not isinstance(dados, dict):
            return make_response(jsonify({"erro": "O corpo da requisição deve ser um objeto JSON."}), 400)
        resultado = PaymentService.cancelar_tentativa_paypal(pedido_id, account_id, account_type, dados.get("token"))
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "pagamento": resultado.get("dados")}), 200)

    @staticmethod
    def capturar_paypal(pedido_id, account_id, account_type, dados):
        if not isinstance(dados, dict):
            return make_response(jsonify({"erro": "O corpo da requisição deve ser um objeto JSON."}), 400)
        resultado = PaymentService.capturar_paypal(pedido_id, account_id, account_type, dados.get("token"))
        if not resultado["success"]:
            body = {"erro": resultado["erro"]}
            if resultado.get("dados"):
                body["pagamento"] = resultado["dados"]
            if resultado.get("pedido"):
                body["pedido"] = resultado["pedido"]
            return make_response(jsonify(body), resultado["status_code"])
        body = {"mensagem": resultado.get("mensagem", "Captura PayPal processada.")}
        if resultado.get("dados"):
            body["pagamento"] = resultado["dados"]
        if resultado.get("pedido"):
            body["pedido"] = resultado["pedido"]
        return make_response(jsonify(body), 200)

    @staticmethod
    def webhook_paypal(headers, raw_body):
        resultado = PaymentService.processar_webhook_paypal(headers, raw_body)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado.get("mensagem", "Webhook PayPal recebido."), "ok": True}), 200)

    @staticmethod
    def webhook_mercado_pago(headers, raw_body, query_data_id=None):
        resultado = PaymentService.processar_webhook_mercado_pago(
            headers, raw_body, query_data_id
        )
        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}), resultado["status_code"]
            )
        return make_response(
            jsonify({"mensagem": resultado.get("mensagem", "Webhook recebido."), "ok": True}),
            200,
        )

