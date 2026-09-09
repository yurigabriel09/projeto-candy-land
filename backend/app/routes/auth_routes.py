from flask import Blueprint, request

from app.controllers.auth_controller import AuthController

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["POST"])
def solicitar_codigo():
    return AuthController.solicitar_codigo(request.get_json() or {})

@auth_bp.route("/verify", methods=["POST"])
def verificar_codigo():
    return AuthController.verificar_codigo(request.get_json() or {})