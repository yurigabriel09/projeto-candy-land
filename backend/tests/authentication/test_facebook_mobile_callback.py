from urllib.parse import parse_qs, urlencode, urlparse

from app.routes.auth_routes import auth_bp
from app.services.facebook_auth_service import FacebookAuthService
from flask import Flask


def _oauth_app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret", APP_ENV="testing")
    app.register_blueprint(auth_bp)
    return app


def _state_from_start(client, platform="ANDROID", audience="PERSONAL"):
    inicio = client.get(
        f"/auth/facebook?platform={platform}&audiencia={audience}"
    )
    parametros = parse_qs(urlparse(inicio.headers["Location"]).query)
    return parametros["state"][0]


def test_callback_facebook_android_redireciona_para_deep_link(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FACEBOOK_CLIENT_ID", "facebook-app-id")
    monkeypatch.setenv(
        "FACEBOOK_REDIRECT_URI", "http://localhost:5000/auth/facebook/callback"
    )
    monkeypatch.setenv(
        "FACEBOOK_MOBILE_REDIRECT_URI", "com.candyland.mobile://oauth/facebook"
    )
    monkeypatch.setattr(
        FacebookAuthService,
        "processar_callback",
        staticmethod(lambda code: "ticket-mobile-assinado"),
    )

    client = _oauth_app().test_client()
    state = _state_from_start(client)
    callback = client.get(
        "/auth/facebook/callback?" + urlencode({"code": "codigo-valido", "state": state})
    )

    destino = urlparse(callback.headers["Location"])
    parametros = parse_qs(destino.query)
    assert callback.status_code == 302
    assert destino.scheme == "com.candyland.mobile"
    assert destino.netloc == "oauth"
    assert destino.path == "/facebook"
    assert parametros["facebook_ticket"] == ["ticket-mobile-assinado"]
    assert callback.headers["Cache-Control"] == "no-store"


def test_callback_facebook_android_sem_cookie_de_sessao_nao_volta_para_web(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FACEBOOK_MOBILE_REDIRECT_URI", "com.candyland.mobile://oauth/facebook")
    state_client = _oauth_app().test_client()
    state = _state_from_start(state_client)

    # Simula o navegador não reenviando o cookie: o state assinado ainda preserva
    # que a origem é Android, então o erro volta ao deep link, não ao frontend web.
    callback_client = _oauth_app().test_client()
    callback = callback_client.get(
        "/auth/facebook/callback?" + urlencode({"code": "codigo-valido", "state": state})
    )

    destino = urlparse(callback.headers["Location"])
    parametros = parse_qs(destino.query)
    assert destino.scheme == "com.candyland.mobile"
    assert destino.netloc == "oauth"
    assert destino.path == "/facebook"
    assert "facebook_error" in parametros


def test_callback_facebook_web_continua_redirecionando_para_frontend(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FRONTEND_URL", "https://frontend.example.test")
    monkeypatch.setattr(
        FacebookAuthService,
        "processar_callback",
        staticmethod(lambda code: "ticket-web-assinado"),
    )

    client = _oauth_app().test_client()
    state = _state_from_start(client, platform="WEB", audience="PERSONAL")
    callback = client.get(
        "/auth/facebook/callback?" + urlencode({"code": "codigo-valido", "state": state})
    )

    destino = urlparse(callback.headers["Location"])
    parametros = parse_qs(destino.query)
    assert destino.scheme == "https"
    assert destino.netloc == "frontend.example.test"
    assert destino.path == "/login"
    assert parametros["facebook_ticket"] == ["ticket-web-assinado"]
