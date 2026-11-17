from app.services.report_service import ReportService
from flask import jsonify, make_response

# Tipos de conta já existentes: "PERSONAL" (cliente) e "BUSINESS" (restaurante).
TIPO_CONTA_LOJA = "BUSINESS"


class ReportController:
    @staticmethod
    def relatorio_loja(account_id, tipo_conta):
        if tipo_conta != TIPO_CONTA_LOJA:
            return make_response(
                jsonify({"erro": "Apenas restaurantes podem acessar este relatório."}),
                403,
            )
        resultado = ReportService.relatorio_loja(account_id)
        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}), resultado["status_code"]
            )
        return make_response(
            jsonify({"mensagem": resultado["mensagem"], "relatorio": resultado["dados"]}),
            200,
        )

    @staticmethod
    def relatorio_admin():
        # DEMONSTRAÇÃO: não há usuário administrador no projeto, então este
        # relatório é público (sem autenticação). Proteger antes de ir a produção.
        resultado = ReportService.relatorio_admin()
        if not resultado["success"]:
            return make_response(
                jsonify({"erro": resultado["erro"]}), resultado["status_code"]
            )
        return make_response(
            jsonify({"mensagem": resultado["mensagem"], "relatorio": resultado["dados"]}),
            200,
        )
