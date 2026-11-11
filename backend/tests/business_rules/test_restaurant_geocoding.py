from datetime import datetime, timedelta

import pytest
from flask import Flask

from app.database.database import db
from app.models.auth_attempt import TentativaAutenticacao
from app.services.restaurant_service import RestauranteService


@pytest.fixture
def app():
    application = Flask("restaurant_geocoding_test")
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="restaurant-geocoding-test-secret",
        GOOGLE_MAPS_GEOCODING_API_KEY="",
    )
    db.init_app(application)
    with application.app_context():
        db.create_all()
        tentativa = TentativaAutenticacao(
            canal_inicial="EMAIL",
            email="geo@example.com",
            telefone="+5511999997777",
            email_validado=True,
            telefone_validado=True,
            concluida=True,
            expira_em=datetime.utcnow() + timedelta(minutes=10),
        )
        db.session.add(tentativa)
        db.session.commit()
        application.config["TEST_ATTEMPT_ID"] = tentativa.id
        yield application
        db.session.remove()
        db.engine.dispose()


def _address():
    return {
        "cep": "01001-000",
        "rua": "Praça da Sé",
        "numero": "100",
        "bairro": "Sé",
        "cidade": "São Paulo",
        "estado": "SP",
    }


def test_geocoding_sem_chave_retorna_fallback_manual(app):
    with app.app_context():
        result = RestauranteService._geocodificar_dados_endereco(_address())
    assert result["success"] is False
    assert result["status_code"] == 503
    assert "coordenadas manuais" in result["erro"]


def test_geocoding_retorna_coordenadas_sem_expor_a_chave(app, monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "OK",
                "results": [{
                    "formatted_address": "Praça da Sé, São Paulo - SP, Brasil",
                    "geometry": {"location": {"lat": -23.5505208, "lng": -46.6333081}},
                }],
            }

    def fake_get(url, params, timeout):
        calls.update(url=url, params=params, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr("app.services.restaurant_service.requests.get", fake_get)
    with app.app_context():
        app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "google-test-secret"
        result = RestauranteService._geocodificar_dados_endereco(_address())

    assert result["success"] is True
    assert result["dados"]["latitude"] == -23.550521
    assert result["dados"]["longitude"] == -46.633308
    assert calls["params"]["key"] == "google-test-secret"
    assert calls["timeout"] == 8


def test_geocoding_de_cadastro_exige_tentativa_verificada(app):
    with app.app_context():
        result = RestauranteService.geocodificar_endereco_cadastro({
            "tentativa_id": "tentativa-inexistente",
            "endereco": _address(),
        })
    assert result["success"] is False
    assert result["status_code"] == 401
