import hmac
import os
import secrets
from urllib.parse import urlencode

from app.controllers.auth_controller import AuthController
from app.services.facebook_auth_service import FacebookAuthService
from flask import Blueprint, current_app, redirect, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.after_request
def impedir_cache_de_respostas_de_autenticacao(response):
    """Evita armazenar em cache respostas que podem conter dados de sessão."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


_FACEBOOK_STATE_COOKIE = "candyland_facebook_oauth_state"
_FACEBOOK_AUDIENCE_COOKIE = "candyland_facebook_oauth_audience"
_FACEBOOK_PLATFORM_COOKIE = "candyland_facebook_oauth_platform"
_FACEBOOK_CALLBACK_PATH = "/auth/facebook/callback"
_FACEBOOK_STATE_SALT = "candyland-facebook-oauth-state"
_FACEBOOK_STATE_MAX_AGE = 300
_NON_PRODUCTION_ENVS = {"development", "dev", "local", "test", "testing"}


def _facebook_cookie_secure():
    ambiente = str(
        current_app.config.get("APP_ENV", os.getenv("APP_ENV", "production"))
    ).strip().lower()
    return ambiente not in _NON_PRODUCTION_ENVS


def _facebook_state_serializer():
    """Assina o state para que a plataforma não dependa do retorno de cookies."""
    secret_key = current_app.config.get("SECRET_KEY") or os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY não configurado para autenticação do Facebook.")
    return URLSafeTimedSerializer(secret_key, salt=_FACEBOOK_STATE_SALT)


def _dados_state_facebook(state):
    """Valida a assinatura e a validade temporal do state recebido do Facebook."""
    if not state:
        return None
    try:
        dados = _facebook_state_serializer().loads(
            state, max_age=_FACEBOOK_STATE_MAX_AGE
        )
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return None

    if not isinstance(dados, dict) or not dados.get("nonce"):
        return None

    plataforma = str(dados.get("plataforma", "WEB")).strip().upper()
    audiencia = str(dados.get("audiencia", "PERSONAL")).strip().upper()
    if plataforma not in {"WEB", "ANDROID"}:
        plataforma = "WEB"
    if audiencia not in {"PERSONAL", "BUSINESS"}:
        audiencia = "PERSONAL"

    return {"plataforma": plataforma, "audiencia": audiencia}


def _redirecionar_login_facebook(
    plataforma=None, audiencia=None, **parametros
):
    # A informação assinada no state é prioritária. Os cookies são mantidos para
    # compatibilidade com o fluxo web e com clientes que já dependem deles.
    plataforma = (
        str(plataforma or request.cookies.get(_FACEBOOK_PLATFORM_COOKIE, "WEB"))
        .strip()
        .upper()
    )
    audiencia = (
        str(audiencia or request.cookies.get(_FACEBOOK_AUDIENCE_COOKIE, "PERSONAL"))
        .strip()
        .upper()
    )

    if plataforma == "ANDROID":
        # URI fixo e controlado pela configuração do backend: nunca aceitar
        # redirect_uri arbitrário vindo do aplicativo.
        mobile_uri = os.getenv(
            "FACEBOOK_MOBILE_REDIRECT_URI",
            "com.candyland.mobile://oauth/facebook",
        ).strip()
        mobile_parametros = {}
        if parametros.get("facebook_ticket"):
            mobile_parametros["ticket"] = parametros["facebook_ticket"]
        if parametros.get("facebook_error"):
            mobile_parametros["error"] = parametros["facebook_error"]
        destino = mobile_uri + (
            "?" + urlencode(mobile_parametros) if mobile_parametros else ""
        )
        resposta = redirect(destino)
    else:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
        caminho_login = "/parceiros/login" if audiencia == "BUSINESS" else "/login"
        resposta = redirect(f"{frontend_url}{caminho_login}?" + urlencode(parametros))

    # Sempre limpar os dois cookies históricos esperados pelo fluxo web. O cookie
    # de plataforma só é criado no Android e também é removido quando existir.
    cookies_para_limpar = [_FACEBOOK_STATE_COOKIE, _FACEBOOK_AUDIENCE_COOKIE]
    if request.cookies.get(_FACEBOOK_PLATFORM_COOKIE):
        cookies_para_limpar.append(_FACEBOOK_PLATFORM_COOKIE)

    for nome_cookie in cookies_para_limpar:
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
        audiencia = request.args.get("audiencia", "PERSONAL").strip().upper()
        if audiencia not in {"PERSONAL", "BUSINESS"}:
            audiencia = "PERSONAL"

        plataforma = request.args.get("platform", "WEB").strip().upper()
        if plataforma not in {"WEB", "ANDROID"}:
            plataforma = "WEB"

        # O state assinado carrega plataforma e audiência. Assim, o callback ainda
        # consegue voltar ao Android mesmo quando o navegador não devolve cookies.
        state = _facebook_state_serializer().dumps(
            {
                "nonce": secrets.token_urlsafe(32),
                "audiencia": audiencia,
                "plataforma": plataforma,
            }
        )

        url = FacebookAuthService.gerar_url_autorizacao(state)
        resposta = redirect(url)

        # Mantemos os cookies para compatibilidade com o fluxo web já testado.
        cookies_oauth = [
            (_FACEBOOK_STATE_COOKIE, state),
            (_FACEBOOK_AUDIENCE_COOKIE, audiencia),
        ]
        if plataforma == "ANDROID":
            cookies_oauth.append((_FACEBOOK_PLATFORM_COOKIE, "ANDROID"))

        for nome_cookie, valor_cookie in cookies_oauth:
            resposta.set_cookie(
                nome_cookie,
                valor_cookie,
                max_age=_FACEBOOK_STATE_MAX_AGE,
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

    dados_state = _dados_state_facebook(state)
    cookie_corresponde = bool(
        state and state_cookie and hmac.compare_digest(state, state_cookie)
    )

    # O state assinado é suficiente para recuperar o destino sem cookies. Quando
    # o cookie estiver presente, também rejeitamos divergências contra replay.
    if not dados_state or (state_cookie and not cookie_corresponde):
        return _redirecionar_login_facebook(
            facebook_error=(
                "Não foi possível validar o state do Facebook. Inicie novamente."
            )
        )

    plataforma = dados_state["plataforma"]
    audiencia = dados_state["audiencia"]

    if request.args.get("error"):
        return _redirecionar_login_facebook(
            plataforma=plataforma,
            audiencia=audiencia,
            facebook_error="Autenticação com Facebook cancelada.",
        )

    try:
        ticket = FacebookAuthService.processar_callback(request.args.get("code"))
        return _redirecionar_login_facebook(
            plataforma=plataforma,
            audiencia=audiencia,
            facebook_ticket=ticket,
        )

    except ValueError as erro:
        return _redirecionar_login_facebook(
            plataforma=plataforma,
            audiencia=audiencia,
            facebook_error=str(erro),
        )


@auth_bp.route("/facebook/complete", methods=["POST"])
def completar_facebook():
    return AuthController.completar_facebook(request.get_json() or {})
