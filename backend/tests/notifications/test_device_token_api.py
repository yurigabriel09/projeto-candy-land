import pytest
from app.database.database import db
from app.models import DeviceToken
from app.routes.device_routes import device_bp
from app.services.token_service import TokenService
from flask import Flask


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="test-secret-key",
        JWT_EXPIRATION_HOURS=1,
    )
    db.init_app(app)
    app.register_blueprint(device_bp)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def _headers(account_type="PERSONAL", account_id=7):
    token = TokenService.gerar_token(
        account_type, account_id, f"{account_type.lower()}@example.com"
    )
    return {"Authorization": f"Bearer {token}"}


def test_registro_de_dispositivo_exige_jwt(app):
    response = app.test_client().post("/devices/fcm", json={"token": "fcm-token"})
    assert response.status_code == 401


def test_cliente_pode_registrar_token_fcm_vinculado_a_propria_conta(app):
    response = app.test_client().post(
        "/devices/fcm",
        json={"token": "fcm-token-1", "platform": "ANDROID", "device_id": "device-1"},
        headers=_headers("PERSONAL", 7),
    )
    assert response.status_code == 200
    with app.app_context():
        device = DeviceToken.query.filter_by(token="fcm-token-1").one()
        assert device.account_type == "PERSONAL"
        assert device.account_id == 7
        assert device.platform == "ANDROID"
        assert device.active is True


def test_registro_reassocia_token_a_sessao_autenticada_mais_recente(app):
    client = app.test_client()
    first = client.post(
        "/devices/fcm", json={"token": "shared-token"}, headers=_headers("PERSONAL", 7)
    )
    second = client.post(
        "/devices/fcm", json={"token": "shared-token"}, headers=_headers("BUSINESS", 12)
    )
    assert first.status_code == second.status_code == 200
    with app.app_context():
        assert DeviceToken.query.filter_by(token="shared-token").count() == 1
        device = DeviceToken.query.filter_by(token="shared-token").one()
        assert (device.account_type, device.account_id) == ("BUSINESS", 12)


def test_conta_so_remove_o_proprio_token_fcm(app):
    client = app.test_client()
    client.post(
        "/devices/fcm", json={"token": "owned-token"}, headers=_headers("PERSONAL", 7)
    )
    forbidden = client.delete(
        "/devices/fcm", json={"token": "owned-token"}, headers=_headers("PERSONAL", 8)
    )
    assert forbidden.status_code == 200  # Idempotente; não apaga token alheio.
    with app.app_context():
        assert DeviceToken.query.filter_by(token="owned-token").count() == 1
    removed = client.delete(
        "/devices/fcm", json={"token": "owned-token"}, headers=_headers("PERSONAL", 7)
    )
    assert removed.status_code == 200
    with app.app_context():
        assert DeviceToken.query.filter_by(token="owned-token").count() == 0


def test_token_vazio_ou_plataforma_invalida_e_rejeitado(app):
    client = app.test_client()
    empty = client.post("/devices/fcm", json={"token": " "}, headers=_headers())
    invalid = client.post(
        "/devices/fcm",
        json={"token": "valid-token", "platform": "UNKNOWN"},
        headers=_headers(),
    )
    assert empty.status_code == 400
    assert invalid.status_code == 400


def test_push_e_ignorado_com_seguranca_quando_fcm_nao_esta_configurado(app):
    from types import SimpleNamespace

    from app.services.push_notification_service import PushNotificationService

    with app.app_context():
        app.config["FCM_PROJECT_ID"] = ""
        app.config["FCM_SERVICE_ACCOUNT_FILE"] = ""
        pedido = SimpleNamespace(id=1, status="PENDENTE_PAGAMENTO")
        resultado = PushNotificationService.notificar_pedido(pedido)
        assert resultado["sent"] == 0
        assert resultado["skipped"] is True
