from decimal import Decimal

import pytest
from flask import Flask

from app.database.database import db
from app.models.address import Endereco
from app.models.user import Usuario
from app.services.user_service import UserService


@pytest.fixture
def app():
    application = Flask("address_geocoding_test")
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="geocoding-test-secret",
        GOOGLE_MAPS_GEOCODING_API_KEY="",
    )
    db.init_app(application)
    with application.app_context():
        db.create_all()
        user = Usuario(
            nome_completo="Cliente Geocoding",
            email="geocoding@example.com",
            telefone="+5511999998888",
            cpf="12345678901",
        )
        db.session.add(user)
        db.session.flush()
        address = Endereco(
            id_usuario=user.id,
            cep="01001-000",
            rua="Praça da Sé",
            numero="100",
            bairro="Sé",
            cidade="São Paulo",
            estado="SP",
            tipo_endereco="RESIDENCIAL",
            principal=True,
            ativo=True,
        )
        db.session.add(address)
        db.session.commit()
        application.config["TEST_USER_ID"] = user.id
        application.config["TEST_ADDRESS_ID"] = address.id
        yield application
        db.session.remove()
        db.engine.dispose()


def test_geocoding_explica_quando_chave_nao_esta_configurada(app):
    with app.app_context():
        resultado = UserService.geocodificar_endereco(
            app.config["TEST_USER_ID"], app.config["TEST_ADDRESS_ID"]
        )
    assert resultado["success"] is False
    assert resultado["status_code"] == 503
    assert "GOOGLE_MAPS_GEOCODING_API_KEY" in resultado["erro"]


def test_geocoding_persiste_coordenadas_encontradas(app, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "OK",
                "results": [{
                    "formatted_address": "Praça da Sé, São Paulo - SP, Brasil",
                    "geometry": {"location": {"lat": -23.55052, "lng": -46.633308}},
                }],
            }

    chamadas = {}

    def fake_get(url, params, timeout):
        chamadas.update(url=url, params=params, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr("app.services.user_service.requests.get", fake_get)
    with app.app_context():
        app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "google-test-key"
        resultado = UserService.geocodificar_endereco(
            app.config["TEST_USER_ID"], app.config["TEST_ADDRESS_ID"]
        )
        address = db.session.get(Endereco, app.config["TEST_ADDRESS_ID"])
        assert resultado["success"] is True
        assert Decimal(str(address.latitude)) == Decimal("-23.550520")
        assert Decimal(str(address.longitude)) == Decimal("-46.633308")
    assert chamadas["params"]["key"] == "google-test-key"
    assert chamadas["params"]["components"] == "country:BR"
    assert chamadas["timeout"] == 8


def test_geocoding_nao_permite_localizar_endereco_de_outro_cliente(app):
    with app.app_context():
        resultado = UserService.geocodificar_endereco(
            app.config["TEST_USER_ID"] + 999, app.config["TEST_ADDRESS_ID"]
        )
    assert resultado["success"] is False
    assert resultado["status_code"] == 404
