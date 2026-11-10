from urllib.parse import parse_qs, urlencode, urlparse

from flask import Flask

from app.routes.auth_routes import auth_bp
from app.services.facebook_auth_service import FacebookAuthService


def _oauth_app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret", APP_ENV="testing")
    app.register_blueprint(auth_bp)
    return app


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

    inicio = client.get("/auth/facebook?platform=ANDROID&audiencia=PERSONAL")
    parametros = parse_qs(urlparse(inicio.headers["Location"]).query)
    state = parametros["state"][0]
    cookies_inicio = "\n".join(inicio.headers.getlist("Set-Cookie"))
    assert "candyland_facebook_oauth_platform=ANDROID" in cookies_inicio

    callback = client.get(
        "/auth/facebook/callback?" + urlencode({"code": "codigo-valido", "state": state})
    )
    destino = urlparse(callback.headers["Location"])
    query = parse_qs(destino.query)

    assert callback.status_code == 302
    assert destino.scheme == "com.candyland.mobile"
    assert destino.netloc == "oauth"
    assert destino.path == "/facebook"
    assert query["ticket"] == ["ticket-mobile-assinado"]
    cookies_callback = "\n".join(callback.headers.getlist("Set-Cookie"))
    assert "candyland_facebook_oauth_platform" in cookies_callback
    assert callback.headers["Cache-Control"] == "no-store"
