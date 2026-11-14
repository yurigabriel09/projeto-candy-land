from datetime import UTC, datetime, timedelta

import pytest
from app.database.database import db
from app.models import CodigoAutenticacao, TentativaAutenticacao, Usuario
from app.services.auth_service import AuthService
from app.services.google_auth_service import GoogleAuthService
from flask import Flask
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="single-channel-auth-test-secret",
        JWT_EXPIRATION_HOURS=1,
        APP_ENV="testing",
        ALLOW_DUPLICATE_PHONE=False,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def _create_user(email="cliente@example.com", phone="+5511999990000", cpf="12345678901"):
    user = Usuario(
        nome_completo="Cliente de Teste",
        email=email,
        telefone=phone,
        cpf=cpf,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _mock_otp_sender(monkeypatch):
    def send_code(attempt, channel, destination):
        db.session.add(
            CodigoAutenticacao(
                tentativa_id=attempt.id,
                tipo=channel,
                destino=destination,
                codigo_hash=generate_password_hash("123456"),
                expira_em=(
                    datetime.now(UTC).replace(tzinfo=None)
                    + timedelta(minutes=10)
                ),
                usado=False,
            )
        )
        return {"success": True, "mensagem": "Código enviado para teste."}

    monkeypatch.setattr(
        AuthService, "_gerar_e_enviar_codigo", staticmethod(send_code)
    )


def test_login_de_conta_existente_so_com_email(app, monkeypatch):
    with app.app_context():
        _create_user()
        _mock_otp_sender(monkeypatch)

        start = AuthService.iniciar_autenticacao("EMAIL", "CLIENTE@example.com")
        assert start["success"] is True

        attempt = db.session.get(TentativaAutenticacao, start["tentativa_id"])
        assert attempt.email == "cliente@example.com"
        # O telefone vem da conta já encontrada; o cliente não precisa digitá-lo.
        assert attempt.telefone == "+5511999990000"

        result = AuthService.verificar_codigo(start["tentativa_id"], "123456")
        assert result["success"] is True
        assert result["dados"]["tipo_conta"] == "PERSONAL"
        assert result["dados"]["email"] == "cliente@example.com"
        assert result["dados"]["token"]
        assert attempt.concluida is True


def test_login_de_conta_existente_so_com_celular(app, monkeypatch):
    with app.app_context():
        user = _create_user()
        _mock_otp_sender(monkeypatch)

        start = AuthService.iniciar_autenticacao("WHATSAPP", "(11) 99999-0000")
        assert start["success"] is True

        attempt = db.session.get(TentativaAutenticacao, start["tentativa_id"])
        assert attempt.telefone == "+5511999990000"
        # O e-mail é recuperado internamente da conta, sem pedir outro campo.
        assert attempt.email == "cliente@example.com"

        result = AuthService.verificar_codigo(start["tentativa_id"], "123456")
        assert result["success"] is True
        assert result["dados"]["tipo_conta"] == "PERSONAL"
        assert result["dados"]["id"] == user.id
        assert result["dados"]["token"]
        assert attempt.concluida is True


def test_novo_cadastro_pede_contato_que_ainda_nao_foi_informado(app, monkeypatch):
    with app.app_context():
        _mock_otp_sender(monkeypatch)

        start = AuthService.iniciar_autenticacao("EMAIL", "novo@example.com")
        assert start["success"] is True

        attempt = db.session.get(TentativaAutenticacao, start["tentativa_id"])
        assert attempt.telefone is None

        result = AuthService.verificar_codigo(start["tentativa_id"], "123456")
        assert result["success"] is True
        assert result.get("dados") is None
        assert result["proximo_canal"] == "WHATSAPP"
        assert result["tentativa_id"] == start["tentativa_id"]


def test_celular_compartilhado_em_varias_contas_nao_autentica_conta_aleatoria(app):
    with app.app_context():
        app.config.update(APP_ENV="testing", ALLOW_DUPLICATE_PHONE=True)
        _create_user("um@example.com", "+5511999990000", "12345678901")
        _create_user("dois@example.com", "+5511999990000", "98765432100")

        result = AuthService.iniciar_autenticacao("WHATSAPP", "+5511999990000")
        assert result["success"] is False
        assert result["status_code"] == 409
        assert "mais de uma conta" in result["erro"].lower()


def test_google_login_de_conta_existente_entrega_sessao_sem_otp_adicional(app, monkeypatch):
    with app.app_context():
        user = _create_user()
        monkeypatch.setattr(
            GoogleAuthService,
            "validar_credencial",
            staticmethod(lambda credential: {"email": user.email}),
        )

        result = AuthService.autenticar_google("google-id-token-validado")
        assert result["success"] is True
        assert result["dados"]["tipo_conta"] == "PERSONAL"
        assert result["dados"]["id"] == user.id
        assert result["dados"]["token"]
        assert TentativaAutenticacao.query.count() == 0


def test_facebook_login_de_conta_existente_entrega_sessao_sem_otp_adicional(app):
    with app.app_context():
        user = _create_user()

        result = AuthService.autenticar_facebook(
            {"id": "facebook-user-123", "email": user.email}
        )
        assert result["success"] is True
        assert result["dados"]["tipo_conta"] == "PERSONAL"
        assert result["dados"]["id"] == user.id
        assert result["dados"]["token"]
        assert TentativaAutenticacao.query.count() == 0
