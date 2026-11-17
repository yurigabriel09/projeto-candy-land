from datetime import UTC, datetime, timedelta

import pytest
from app.database.database import db
from app.models.auth_attempt import TentativaAutenticacao
from app.routes.restaurant_routes import restaurante_bp
from app.services.restaurant_service import RestauranteService
from flask import Flask


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
    application.register_blueprint(restaurante_bp)
    with application.app_context():
        db.create_all()
        tentativa = TentativaAutenticacao(
            canal_inicial="EMAIL",
            email="geo@example.com",
            telefone="+5511999997777",
            email_validado=True,
            telefone_validado=True,
            concluida=True,
            expira_em=datetime.now(UTC).replace(tzinfo=None)
            + timedelta(minutes=10),
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


def test_geocoding_sem_chave_exige_configuracao_do_provedor(app):
    with app.app_context():
        result = RestauranteService._geocodificar_dados_endereco(_address())
    assert result["success"] is False
    assert result["status_code"] == 503
    assert "GOOGLE_MAPS_GEOCODING_API_KEY" in result["erro"]


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

    monkeypatch.setattr("app.services.geocoding_service.requests.get", fake_get)
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


def test_geocoding_publico_retorna_coordenadas_sem_persistir_dados(app, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "OK",
                "results": [{
                    "formatted_address": "Rua Haddock Lobo, São Paulo - SP, Brasil",
                    "geometry": {"location": {"lat": -23.5581, "lng": -46.6602}},
                }],
            }

    calls = {}

    def fake_get(url, params, timeout):
        calls.update(url=url, params=params, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr("app.services.geocoding_service.requests.get", fake_get)
    with app.app_context():
        app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "google-test-secret"
        response = app.test_client().post(
            "/restaurantes/geocodificar-endereco/publico",
            json={"endereco": "Rua Haddock Lobo, 123, São Paulo, SP"},
        )

    assert response.status_code == 200
    payload = response.get_json()["dados"]
    assert payload["latitude"] == -23.5581
    assert payload["longitude"] == -46.6602
    assert calls["params"]["key"] == "google-test-secret"
    assert calls["timeout"] == 8


def test_geocoding_publico_sem_chave_retorna_503_sem_autenticacao(app):
    response = app.test_client().post(
        "/restaurantes/geocodificar-endereco/publico",
        json={"endereco": "Rua Haddock Lobo, 123, São Paulo, SP"},
    )
    assert response.status_code == 503
    assert "GOOGLE_MAPS_GEOCODING_API_KEY" in response.get_json()["erro"]


def test_geocoding_chave_recusada_retorna_503(app, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "REQUEST_DENIED", "results": []}

    monkeypatch.setattr(
        "app.services.geocoding_service.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )
    with app.app_context():
        app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "google-test-secret"
        result = RestauranteService._geocodificar_dados_endereco(_address())
    assert result["success"] is False
    assert result["status_code"] == 503
    assert "Google recusou" in result["erro"]
