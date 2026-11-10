import hmac
import os
import secrets
from urllib.parse import urlencode

from app.controllers.auth_controller import AuthController
from app.services.facebook_auth_service import FacebookAuthService
from flask import Blueprint, current_app, redirect, request

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.after_request
def impedir_cache_de_respostas_de_autenticacao(response):
    """Evita armazenar em cache respostas que podem conter dados de sessão."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response

_FACEBOOK_STATE_COOKIE = "candyland_facebook_oauth_state"
_FACEBOOK_AUDIENCE_COOKIE = "candyland_facebook_oauth_audience"
_FACEBOOK_CALLBACK_PATH = "/auth/facebook/callback"
_NON_PRODUCTION_ENVS = {"development", "dev", "local", "test", "testing"}


def _facebook_cookie_secure():
    ambiente = str(
        current_app.config.get("APP_ENV", os.getenv("APP_ENV", "production"))
    ).strip().lower()
    return ambiente not in _NON_PRODUCTION_ENVS


def _redirecionar_login_facebook(**parametros):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    audiencia = request.cookies.get(_FACEBOOK_AUDIENCE_COOKIE, "PERSONAL")
    caminho_login = "/parceiros/login" if audiencia == "BUSINESS" else "/login"
    resposta = redirect(f"{frontend_url}{caminho_login}?" + urlencode(parametros))
    for nome_cookie in (_FACEBOOK_STATE_COOKIE, _FACEBOOK_AUDIENCE_COOKIE):
        resposta.delete_cookie(
            nome_cookie,
            path=_FACEBOOK_CALLBACK_PATH,
            httponly=True,
            secure=_facebook_cookie_secure(),
            samesite="Lax",
        )
    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["Pragma"] = "no-cache"
    return resposta


@auth_bp.route("/login", methods=["POST"])
def solicitar_codigo():
    return AuthController.solicitar_codigo(request.get_json() or {})


@auth_bp.route("/second-code", methods=["POST"])
def solicitar_segundo_codigo():
    return AuthController.solicitar_segundo_codigo(request.get_json() or {})


@auth_bp.route("/verify", methods=["POST"])
def verificar_codigo():
    return AuthController.verificar_codigo(request.get_json() or {})


@auth_bp.route("/google", methods=["POST"])
def autenticar_google():
    return AuthController.autenticar_google(request.get_json() or {})


@auth_bp.route("/facebook", methods=["GET"])
def autenticar_facebook():
    try:
        state = secrets.token_urlsafe(32)
        audiencia = request.args.get("audiencia", "PERSONAL").strip().upper()
        if audiencia not in {"PERSONAL", "BUSINESS"}:
            audiencia = "PERSONAL"

        url = FacebookAuthService.gerar_url_autorizacao(state)
        resposta = redirect(url)
        for nome_cookie, valor_cookie in (
            (_FACEBOOK_STATE_COOKIE, state),
            (_FACEBOOK_AUDIENCE_COOKIE, audiencia),
        ):
            resposta.set_cookie(
                nome_cookie,
                valor_cookie,
                max_age=300,
                httponly=True,
                secure=_facebook_cookie_secure(),
                samesite="Lax",
                path=_FACEBOOK_CALLBACK_PATH,
            )
        resposta.headers["Cache-Control"] = "no-store"
        resposta.headers["Pragma"] = "no-cache"
        return resposta

    except ValueError as erro:
        return {"erro": str(erro)}, 500


@auth_bp.route("/facebook/callback", methods=["GET"])
def callback_facebook():
    state = request.args.get("state", "")
    state_cookie = request.cookies.get(_FACEBOOK_STATE_COOKIE, "")

    if not state or not state_cookie or not hmac.compare_digest(state, state_cookie):
        return _redirecionar_login_facebook(
            facebook_error="Não foi possível validar a autenticação com Facebook. Inicie novamente."
        )

    if request.args.get("error"):
        return _redirecionar_login_facebook(
            facebook_error="Autenticação com Facebook cancelada."
        )

    try:
        ticket = FacebookAuthService.processar_callback(request.args.get("code"))
        return _redirecionar_login_facebook(facebook_ticket=ticket)

    except ValueError as erro:
        return _redirecionar_login_facebook(facebook_error=str(erro))


@auth_bp.route("/facebook/complete", methods=["POST"])
def completar_facebook():
    return AuthController.completar_facebook(request.get_json() or {})
