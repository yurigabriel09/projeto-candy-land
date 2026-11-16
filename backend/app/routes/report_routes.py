from app.controllers.report_controller import ReportController
from app.utils.auth_decorator import token_required
from flask import Blueprint, g

relatorio_bp = Blueprint("report", __name__, url_prefix="/relatorios")


@relatorio_bp.route("/loja", methods=["GET"])
@token_required
def relatorio_loja():
    return ReportController.relatorio_loja(
        int(g.current_account_id), g.current_account_type
    )


# DEMONSTRAÇÃO: rota pública (sem @token_required), usada pela página inicial.
@relatorio_bp.route("/admin", methods=["GET"])
def relatorio_admin():
    return ReportController.relatorio_admin()


# TODO: GET /relatorios/cliente (protótipo ainda não definido)
