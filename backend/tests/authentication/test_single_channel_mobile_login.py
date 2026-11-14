from datetime import UTC, datetime, timedelta

import pytest
from app.database.database import db
from app.models import CodigoAutenticacao, Restaurante, TentativaAutenticacao, Usuario
from app.services.auth_service import AuthService
from app.services.google_auth_service import GoogleAuthService
from flask import Flask
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="single-channel-auth-test-secret", JWT_EXPIRATION_HOURS=1,
        APP_ENV="testing", ALLOW_DUPLICATE_PHONE=True,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def _create_user(email="cliente@example.com", phone="+5511999990000", cpf="12345678901"):
    user = Usuario(nome_completo="Cliente de Teste", email=email, telefone=phone, cpf=cpf)
    db.session.add(user)
    db.session.commit()
    return user


def _create_restaurant(email, phone):
    item = Restaurante(cnpj="12345678000199", razao_social="Doceria Teste LTDA", nome="Doceria Teste", cpf_responsavel="98765432100", email=email, telefone=phone)
    db.session.add(item)
    db.session.commit()
    return item


def _mock_otp_sender(monkeypatch):
    def send_code(attempt, channel, destination):
        db.session.add(CodigoAutenticacao(
            tentativa_id=attempt.id, tipo=channel, destino=destination,
            codigo_hash=generate_password_hash("123456"),
            expira_em=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=10), usado=False,
        ))
        return {"success": True, "mensagem": "Código enviado para teste."}
    monkeypatch.setattr(AuthService, "_gerar_e_enviar_codigo", staticmethod(send_code))


def _finish_second_factor(attempt_id, second_channel, second_value):
    requested = AuthService.solicitar_segundo_codigo(attempt_id, second_value)
    assert requested["success"] is True, requested
    return AuthService.verificar_codigo(attempt_id, "123456")


def test_login_por_email_exige_otp_no_celular_e_so_depois_emite_sessao(app, monkeypatch):
    with app.app_context():
        user = _create_user()
        _mock_otp_sender(monkeypatch)
        start = AuthService.iniciar_autenticacao("EMAIL", "CLIENTE@example.com")
        assert start["success"] is True
        attempt = db.session.get(TentativaAutenticacao, start["tentativa_id"])
        assert attempt.email == "cliente@example.com" and attempt.telefone is None
        first = AuthService.verificar_codigo(start["tentativa_id"], "123456")
        assert first["dados"] if first.get("dados") else True
        assert first.get("dados") is None
        assert first["proximo_canal"] == "WHATSAPP"
        final = _finish_second_factor(start["tentativa_id"], "WHATSAPP", user.telefone)
        assert final["success"] is True
        assert final["dados"]["tipo_conta"] == "PERSONAL"
        assert final["dados"]["id"] == user.id
        assert final["dados"]["token"]
        assert attempt.concluida is True


def test_login_por_celular_nao_rejeita_telefone_compartilhado_e_identifica_por_email(app, monkeypatch):
    with app.app_context():
        phone = "+5511999990000"
        user = _create_user("cliente@example.com", phone, "12345678901")
        _create_restaurant("doceria@example.com", phone)
        _mock_otp_sender(monkeypatch)
        start = AuthService.iniciar_autenticacao("WHATSAPP", phone)
        assert start["success"] is True, start
        first = AuthService.verificar_codigo(start["tentativa_id"], "123456")
        assert first.get("dados") is None
        assert first["proximo_canal"] == "EMAIL"
        final = _finish_second_factor(start["tentativa_id"], "EMAIL", user.email)
        assert final["success"] is True, final
        assert final["dados"]["tipo_conta"] == "PERSONAL"
        assert final["dados"]["id"] == user.id


def test_email_e_celular_que_apontam_para_contas_diferentes_sao_rejeitados(app, monkeypatch):
    with app.app_context():
        _create_user("cliente@example.com", "+5511999990000", "12345678901")
        _create_user("outro@example.com", "+5511888880000", "98765432100")
        _mock_otp_sender(monkeypatch)
        start = AuthService.iniciar_autenticacao("EMAIL", "cliente@example.com")
        assert AuthService.verificar_codigo(start["tentativa_id"], "123456")["success"] is True
        response = _finish_second_factor(start["tentativa_id"], "WHATSAPP", "+5511888880000")
        assert response["success"] is False
        assert response["status_code"] == 409
        assert "contas diferentes" in response["erro"].lower() or "não correspondem" in response["erro"].lower()


def test_novo_cadastro_so_e_liberado_depois_dos_dois_fatores(app, monkeypatch):
    with app.app_context():
        _mock_otp_sender(monkeypatch)
        start = AuthService.iniciar_autenticacao("EMAIL", "novo@example.com")
        first = AuthService.verificar_codigo(start["tentativa_id"], "123456")
        assert first.get("dados") is None
        final = _finish_second_factor(start["tentativa_id"], "WHATSAPP", "+5511999991111")
        assert final["success"] is True
        assert final["dados"]["novo_cadastro"] is True
        assert final["dados"]["email"] == "novo@example.com"
        assert final["dados"]["telefone"] == "+5511999991111"
        assert final["dados"]["tentativa_id"] == start["tentativa_id"]


def test_google_existente_tambem_exige_confirmacao_do_celular(app, monkeypatch):
    with app.app_context():
        user = _create_user()
        _mock_otp_sender(monkeypatch)
        monkeypatch.setattr(GoogleAuthService, "validar_credencial", staticmethod(lambda credential: {"email": user.email}))
        start = AuthService.autenticar_google("google-id-token-validado", user.telefone)
        assert start["success"] is True and start.get("dados") is None
        assert start["tentativa_id"]
        final = AuthService.verificar_codigo(start["tentativa_id"], "123456")
        assert final["success"] is True
        assert final["dados"]["id"] == user.id
        assert final["dados"]["token"]


def test_facebook_existente_tambem_exige_confirmacao_do_celular(app, monkeypatch):
    with app.app_context():
        user = _create_user()
        _mock_otp_sender(monkeypatch)
        start = AuthService.autenticar_facebook({"id": "facebook-user-123", "email": user.email}, user.telefone)
        assert start["success"] is True and start.get("dados") is None
        final = AuthService.verificar_codigo(start["tentativa_id"], "123456")
        assert final["success"] is True
        assert final["dados"]["id"] == user.id
        assert final["dados"]["token"]


def test_google_sem_email_de_conta_pede_celular_e_nao_emite_token_direto(app, monkeypatch):
    with app.app_context():
        _mock_otp_sender(monkeypatch)
        monkeypatch.setattr(GoogleAuthService, "validar_credencial", staticmethod(lambda credential: {"email": "novo-google@example.com"}))
        response = AuthService.autenticar_google("google-id-token-validado")
        assert response["success"] is False
        assert response["precisa_telefone"] is True
        assert "token" not in response
