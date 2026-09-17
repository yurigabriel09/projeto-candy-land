from flask import Blueprint, request, redirect
from app.controllers.auth_controller import AuthController
from app.services.facebook_auth_service import FacebookAuthService
from urllib.parse import urlencode
import os


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def solicitar_codigo():
    return AuthController.solicitar_codigo(request.get_json() or {})


@auth_bp.route("/second-code", methods=["POST"])
def solicitar_segundo_codigo():
    return AuthController.solicitar_segundo_codigo(
        request.get_json() or {}
    )


@auth_bp.route("/verify", methods=["POST"])
def verificar_codigo():
    return AuthController.verificar_codigo(
        request.get_json() or {}
    )


@auth_bp.route("/google", methods=["POST"])
def autenticar_google():
    return AuthController.autenticar_google(
        request.get_json() or {}
    )


@auth_bp.route("/facebook", methods=["GET"])
def autenticar_facebook():
    try:
        url = FacebookAuthService.gerar_url_autorizacao()
        return redirect(url)

    except ValueError as erro:
        return {
            "erro": str(erro)
        }, 500


@auth_bp.route("/facebook/callback", methods=["GET"])
def callback_facebook():
    code = request.args.get("code")
    erro = request.args.get("error")

    if erro:
        frontend_url = os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173"
        )

        return redirect(
            f"{frontend_url}/login?" +
            urlencode({
                "facebook_error": "Autenticação com Facebook cancelada."
            })
        )

    try:
        ticket = FacebookAuthService.processar_callback(code)

        frontend_url = os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173"
        )

        return redirect(
            f"{frontend_url}/login?" +
            urlencode({
                "facebook_ticket": ticket
            })
        )

    except ValueError as erro:
        frontend_url = os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173"
        )

        return redirect(
            f"{frontend_url}/login?" +
            urlencode({
                "facebook_error": str(erro)
            })
        )


@auth_bp.route("/facebook/complete", methods=["POST"])
def completar_facebook():
    return AuthController.completar_facebook(
        request.get_json() or {}
    )