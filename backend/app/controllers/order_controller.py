from flask import jsonify, make_response

from app.services.order_service import OrderService


class OrderController:
    @staticmethod
    def criar_pedido(dados, user_id, tipo_conta):
        if tipo_conta != "PERSONAL":
            return make_response(jsonify({"erro": "Apenas clientes podem criar pedidos."}), 403)
        resultado = OrderService.criar_pedido(user_id, dados)
        status = 201 if resultado["success"] else resultado["status_code"]
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), status)
        return make_response(jsonify({"mensagem": resultado["mensagem"], "pedido": resultado["dados"]}), status)

    @staticmethod
    def listar_pedidos(account_id, tipo_conta):
        resultado = OrderService.listar_pedidos(account_id, tipo_conta)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "pedidos": resultado["dados"]}), 200)

    @staticmethod
    def buscar_pedido(pedido_id, account_id, tipo_conta):
        resultado = OrderService.buscar_pedido(pedido_id, account_id, tipo_conta)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "pedido": resultado["dados"]}), 200)

    @staticmethod
    def atualizar_status(pedido_id, dados, account_id, tipo_conta):
        novo_status = dados.get("status")
        if not novo_status:
            return make_response(jsonify({"erro": "O campo status é obrigatório."}), 400)
        resultado = OrderService.atualizar_status(pedido_id, novo_status, account_id, tipo_conta)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"], "pedido": resultado["dados"]}), 200)

    @staticmethod
    def cancelar_pedido(pedido_id, user_id, tipo_conta):
        if tipo_conta != "PERSONAL":
            return make_response(jsonify({"erro": "Apenas clientes podem solicitar cancelamento por esta rota."}), 403)
        resultado = OrderService.cancelar_pedido(pedido_id, user_id)
        if not resultado["success"]:
            return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
        return make_response(jsonify({"mensagem": resultado["mensagem"]}), 200)
