from flask import Flask
import pytest

from app.database.database import db
from app.models.restaurant import Restaurante
from app.routes.restaurant_routes import restaurante_bp
from app.services.token_service import TokenService


@pytest.fixture
def app():
    application = Flask("restaurant_status_test")
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="restaurant-status-test-secret",
    )
    db.init_app(application)
    application.register_blueprint(restaurante_bp)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.engine.dispose()


def _criar_restaurante(status="FECHADO", sufixo="1"):
    restaurante = Restaurante(
        cnpj=f"12345678000{sufixo}",
        razao_social="Doceria Status LTDA",
        nome="Doceria Status",
        cpf_responsavel="12345678901",
        email=f"status{sufixo}@example.com",
        telefone="+5511999997777",
        status=status,
    )
    db.session.add(restaurante)
    db.session.commit()
    return restaurante


def _headers(restaurante_id):
    token = TokenService.gerar_token("BUSINESS", restaurante_id, "status@example.com")
    return {"Authorization": f"Bearer {token}"}


def test_titular_pode_abrir_e_fechar_a_propria_loja(app):
    with app.app_context():
        restaurante = _criar_restaurante("FECHADO")
        client = app.test_client()

        abrir = client.patch(
            f"/restaurantes/{restaurante.id}/status",
            json={"status": "ABERTO"},
            headers=_headers(restaurante.id),
        )
        assert abrir.status_code == 200
        assert abrir.get_json()["dados"]["status"] == "ABERTO"
        assert db.session.get(Restaurante, restaurante.id).status == "ABERTO"

        fechar = client.patch(
            f"/restaurantes/{restaurante.id}/status",
            json={"status": "FECHADO"},
            headers=_headers(restaurante.id),
        )
        assert fechar.status_code == 200
        assert db.session.get(Restaurante, restaurante.id).status == "FECHADO"


def test_loja_em_analise_nao_pode_ser_aberta_pelo_parceiro(app):
    with app.app_context():
        restaurante = _criar_restaurante("EM_ANALISE")
        response = app.test_client().patch(
            f"/restaurantes/{restaurante.id}/status",
            json={"status": "ABERTO"},
            headers=_headers(restaurante.id),
        )
        assert response.status_code == 409
        assert db.session.get(Restaurante, restaurante.id).status == "EM_ANALISE"


def test_status_nao_permite_suspender_ou_aprovar_a_conta(app):
    with app.app_context():
        restaurante = _criar_restaurante("FECHADO")
        response = app.test_client().patch(
            f"/restaurantes/{restaurante.id}/status",
            json={"status": "SUSPENSO"},
            headers=_headers(restaurante.id),
        )
        assert response.status_code == 400
        assert db.session.get(Restaurante, restaurante.id).status == "FECHADO"


def test_outro_restaurante_nao_pode_alterar_status_alheio(app):
    with app.app_context():
        alvo = _criar_restaurante("FECHADO", "1")
        outro = _criar_restaurante("FECHADO", "2")
        response = app.test_client().patch(
            f"/restaurantes/{alvo.id}/status",
            json={"status": "ABERTO"},
            headers=_headers(outro.id),
        )
        assert response.status_code == 403
        assert db.session.get(Restaurante, alvo.id).status == "FECHADO"


def test_alteracao_de_status_exige_token(app):
    with app.app_context():
        restaurante = _criar_restaurante("FECHADO")
        response = app.test_client().patch(
            f"/restaurantes/{restaurante.id}/status", json={"status": "ABERTO"}
        )
        assert response.status_code == 401
