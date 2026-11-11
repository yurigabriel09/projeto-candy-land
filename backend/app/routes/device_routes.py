from flask import Blueprint, g, jsonify, make_response, request

from app.services.device_token_service import DeviceTokenService
from app.utils.auth_decorator import token_required


device_bp = Blueprint("devices", __name__, url_prefix="/devices")


@device_bp.route("/fcm", methods=["POST"])
@token_required
def registrar_token_fcm():
    dados = request.get_json(silent=True) or {}
    resultado = DeviceTokenService.registrar(
        dados.get("token"),
        int(g.current_account_id),
        g.current_account_type,
        dados.get("platform", "ANDROID"),
        dados.get("device_id"),
    )
    if not resultado["success"]:
        return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
    return make_response(jsonify({"mensagem": "Dispositivo registrado para notificações.", "dados": resultado["dados"]}), 200)


@device_bp.route("/fcm", methods=["DELETE"])
@token_required
def remover_token_fcm():
    dados = request.get_json(silent=True) or {}
    resultado = DeviceTokenService.remover(
        dados.get("token"), int(g.current_account_id), g.current_account_type
    )
    if not resultado["success"]:
        return make_response(jsonify({"erro": resultado["erro"]}), resultado["status_code"])
    return make_response(jsonify({"mensagem": "Dispositivo removido das notificações."}), 200)
