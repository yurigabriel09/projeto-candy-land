from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from flask import Flask

from app.routes.auth_routes import auth_bp
from app.services.facebook_auth_service import FacebookAuthService
from app.services.google_auth_service import GoogleAuthService


def test_google_valida_token_e_normaliza_email(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "web-client-id")
    chamadas = {}

    def verificar(credential, request, audience, clock_skew_in_seconds):
        chamadas.update(
            credential=credential,
            audience=audience,
            skew=clock_skew_in_seconds,
        )
        return {
            "email": "Cliente@Example.com",
            "email_verified": True,
            "name": "Cliente Exemplo",
            "sub": "google-sub-123",
        }

    monkeypatch.setattr(
        "app.services.google_auth_service.id_token.verify_oauth2_token", verificar
    )

    resultado = GoogleAuthService.validar_credencial("credential-falsa-para-teste")

    assert resultado == {
        "email": "cliente@example.com",
        "nome": "Cliente Exemplo",
        "google_id": "google-sub-123",
    }
    assert chamadas["credential"] == "credential-falsa-para-teste"
    assert chamadas["audience"] == "web-client-id"
    assert chamadas["skew"] >= 0


def test_google_recusa_credencial_invalida_sem_registrar_claims(monkeypatch, capsys):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "web-client-id")

    def rejeitar(*args, **kwargs):
        raise ValueError("token interno e email-secreto@example.com")

    monkeypatch.setattr(
        "app.services.google_auth_service.id_token.verify_oauth2_token", rejeitar
    )

    with pytest.raises(ValueError, match="Credencial do Google inválida"):
        GoogleAuthService.validar_credencial("token-privado")

    saida = capsys.readouterr()
    assert "token-privado" not in saida.out + saida.err
    assert "email-secreto@example.com" not in saida.out + saida.err
    assert "token interno" not in saida.out + saida.err


def test_google_exige_id_cliente_configurado(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_CLIENT_ID não configurado"):
        GoogleAuthService.validar_credencial("credential")


def test_google_recusa_email_nao_verificado(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "web-client-id")
    monkeypatch.setattr(
        "app.services.google_auth_service.id_token.verify_oauth2_token",
        lambda *args, **kwargs: {
            "email": "cliente@example.com",
            "email_verified": False,
        },
    )

    with pytest.raises(ValueError, match="e-mail do Google não foi verificado"):
        GoogleAuthService.validar_credencial("credential")


def test_facebook_url_exige_e_transmite_state(monkeypatch):
    monkeypatch.setenv("FACEBOOK_CLIENT_ID", "facebook-app-id")
    monkeypatch.setenv(
        "FACEBOOK_REDIRECT_URI", "http://localhost:5000/auth/facebook/callback"
    )

    url = FacebookAuthService.gerar_url_autorizacao("nonce-de-teste")
    parametros = parse_qs(urlparse(url).query)

    assert url.startswith(FacebookAuthService.AUTH_URL + "?")
    assert parametros["client_id"] == ["facebook-app-id"]
    assert parametros["redirect_uri"] == [
        "http://localhost:5000/auth/facebook/callback"
    ]
    assert parametros["state"] == ["nonce-de-teste"]
    assert parametros["response_type"] == ["code"]

    with pytest.raises(ValueError, match="Estado de segurança"):
        FacebookAuthService.gerar_url_autorizacao("")


def test_facebook_intercambia_codigo_e_emite_ticket_assinado(monkeypatch):
    monkeypatch.setenv("FACEBOOK_CLIENT_ID", "facebook-app-id")
    monkeypatch.setenv("FACEBOOK_CLIENT_SECRET", "facebook-app-secret")
    monkeypatch.setenv(
        "FACEBOOK_REDIRECT_URI", "http://localhost:5000/auth/facebook/callback"
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    class RespostaFake:
        def __init__(self, payload, ok=True):
            self.payload = payload
            self.ok = ok

        def json(self):
            return self.payload

    respostas = iter(
        [
            RespostaFake({"access_token": "access-token-falso"}),
            RespostaFake(
                {
                    "id": "facebook-123",
                    "name": "Cliente Facebook",
                    "email": "Cliente@Example.com",
                }
            ),
        ]
    )
    chamadas = []

    def fake_get(url, params, timeout):
        chamadas.append((url, params, timeout))
        return next(respostas)

    monkeypatch.setattr(
        "app.services.facebook_auth_service.requests.get", fake_get
    )

    ticket = FacebookAuthService.processar_callback("authorization-code")
    dados = FacebookAuthService.validar_ticket(ticket)

    assert dados == {
        "id": "facebook-123",
        "nome": "Cliente Facebook",
        "email": "cliente@example.com",
    }
    assert len(chamadas) == 2
    assert chamadas[0][1]["code"] == "authorization-code"
    assert chamadas[0][1]["client_secret"] == "facebook-app-secret"
    assert chamadas[1][1]["access_token"] == "access-token-falso"
    assert all(chamada[2] == 10 for chamada in chamadas)


def test_facebook_rejeita_ticket_alterado(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    with pytest.raises(ValueError, match="Ticket de autenticação do Facebook inválido"):
        FacebookAuthService.validar_ticket("ticket-alterado")


def _app_oauth():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret", APP_ENV="testing")
    app.register_blueprint(auth_bp)
    return app


def test_respostas_de_autenticacao_nao_sao_cacheadas():
    client = _app_oauth().test_client()

    response = client.post("/auth/google", json={})

    assert response.status_code == 400
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"


def _preparar_facebook(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FACEBOOK_CLIENT_ID", "facebook-app-id")
    monkeypatch.setenv(
        "FACEBOOK_REDIRECT_URI", "http://localhost:5000/auth/facebook/callback"
    )
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")


@pytest.mark.parametrize(
    ("audiencia", "caminho_esperado"),
    [("PERSONAL", "/login"), ("BUSINESS", "/parceiros/login")],
)
def test_callback_facebook_exige_state_correspondente_e_limpa_cookie(
    monkeypatch, audiencia, caminho_esperado
):
    _preparar_facebook(monkeypatch)
    monkeypatch.setattr(
        FacebookAuthService,
        "processar_callback",
        staticmethod(lambda code: "ticket-falso"),
    )
    client = _app_oauth().test_client()

    inicio = client.get("/auth/facebook?" + urlencode({"audiencia": audiencia}))
    parametros = parse_qs(urlparse(inicio.headers["Location"]).query)
    state = parametros["state"][0]
    cookies_inicio = "\n".join(inicio.headers.getlist("Set-Cookie"))
    assert "candyland_facebook_oauth_state=" in cookies_inicio
    assert "candyland_facebook_oauth_audience=" in cookies_inicio
    assert "HttpOnly" in cookies_inicio
    assert "SameSite=Lax" in cookies_inicio
    assert "Max-Age=300" in cookies_inicio

    callback = client.get(
        "/auth/facebook/callback?" + urlencode({"code": "code-valido", "state": state})
    )
    destino = parse_qs(urlparse(callback.headers["Location"]).query)

    assert callback.status_code == 302
    assert urlparse(callback.headers["Location"]).netloc == "localhost:5173"
    assert urlparse(callback.headers["Location"]).path == caminho_esperado
    assert destino["facebook_ticket"] == ["ticket-falso"]
    cookies_callback = "\n".join(callback.headers.getlist("Set-Cookie"))
    assert "candyland_facebook_oauth_state=" in cookies_callback
    assert "candyland_facebook_oauth_audience=" in cookies_callback
    assert cookies_callback.count("Max-Age=0") == 2
    assert callback.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("state_query", [None, "outro-state"], ids=["ausente", "diferente"])
def test_callback_facebook_rejeita_state_ausente_ou_diferente(
    monkeypatch, state_query
):
    _preparar_facebook(monkeypatch)

    def callback_nao_deve_ser_chamado(code):
        pytest.fail("O código do provedor não deve ser processado sem state válido")

    monkeypatch.setattr(
        FacebookAuthService,
        "processar_callback",
        staticmethod(callback_nao_deve_ser_chamado),
    )
    client = _app_oauth().test_client()
    inicio = client.get("/auth/facebook")
    state_criado = parse_qs(urlparse(inicio.headers["Location"]).query)["state"][0]
    assert state_criado

    parametros = {"code": "code-valido"}
    if state_query is not None:
        parametros["state"] = state_query
    callback = client.get("/auth/facebook/callback?" + urlencode(parametros))
    destino = parse_qs(urlparse(callback.headers["Location"]).query)

    assert callback.status_code == 302
    mensagem = destino["facebook_error"][0].lower()
    assert "state" in mensagem or "validar" in mensagem
    assert "Max-Age=0" in "\n".join(callback.headers.getlist("Set-Cookie"))


def test_cookie_state_facebook_usa_secure_em_producao(monkeypatch):
    _preparar_facebook(monkeypatch)
    app = _app_oauth()
    app.config["APP_ENV"] = "production"

    resposta = app.test_client().get("/auth/facebook")
    cookies = resposta.headers.getlist("Set-Cookie")

    assert len(cookies) == 2
    assert all("Secure" in cookie for cookie in cookies)
    assert all("HttpOnly" in cookie for cookie in cookies)


def test_callback_facebook_trata_cancelamento_apos_validar_state(monkeypatch):
    _preparar_facebook(monkeypatch)
    client = _app_oauth().test_client()
    inicio = client.get("/auth/facebook")
    state = parse_qs(urlparse(inicio.headers["Location"]).query)["state"][0]

    callback = client.get(
        "/auth/facebook/callback?"
        + urlencode({"error": "access_denied", "state": state})
    )
    destino = parse_qs(urlparse(callback.headers["Location"]).query)

    assert destino["facebook_error"] == ["Autenticação com Facebook cancelada."]
    assert "Max-Age=0" in "\n".join(callback.headers.getlist("Set-Cookie"))
