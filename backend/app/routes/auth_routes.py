from flask import Blueprint, request
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/telefone/enviar-codigo", methods=["POST"])
def enviar_codigo_telefone():
    dados = request.get_json() or {}
    return AuthController.enviar_codigo_telefone(dados)

@auth_bp.route("/email/enviar-codigo", methods=["POST"])
def enviar_codigo_email():
    dados = request.get_json() or {}
    return AuthController.enviar_codigo_email(dados)

@auth_bp.route("/verificar-codigo", methods=["POST"])
def verificar_codigo():
    dados = request.get_json() or {}
    return AuthController.verificar_codigo(dados)

@auth_bp.route("/whatsapp/enviar-codigo", methods=["POST"])
def enviar_codigo_whatsapp():
    dados = request.get_json() or {}
    return AuthController.enviar_codigo_whatsapp(dados)

@auth_bp.route("/whatsapp/verificar-codigo", methods=["POST"])
def verificar_codigo_whatsapp():
    dados = request.get_json() or {}
    return AuthController.verificar_codigo_whatsapp(dados)