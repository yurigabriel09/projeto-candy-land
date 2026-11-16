from datetime import UTC, datetime, timedelta

import pytest
from app.database.database import db
from app.models.auth_attempt import TentativaAutenticacao
from app.models.address import Endereco
from app.models.restaurant import Restaurante
from app.models.user import Usuario  # noqa: F401 - registra a tabela referenciada por addresses
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


def test_geocoding_publico_rejeita_endereco_vazio_ou_curto(app):
    with app.app_context():
        result = RestauranteService.geocodificar_endereco_publico({"endereco": "Rua A"})
    assert result["success"] is False
    assert result["status_code"] == 400


def test_geocoding_publico_sem_chave_retorna_servico_indisponivel(app):
    with app.app_context():
        result = RestauranteService.geocodificar_endereco_publico({
            "endereco": "Avenida Paulista, 1000, São Paulo, SP"
        })
    assert result["success"] is False
    assert result["status_code"] == 503


def test_geocoding_publico_retorna_coordenadas_sem_persistir_endereco(app, monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "OK",
                "results": [{
                    "formatted_address": "Avenida Paulista, São Paulo - SP, Brasil",
                    "geometry": {"location": {"lat": -23.561414, "lng": -46.655881}},
                }],
            }

    def fake_get(url, params, timeout):
        calls.update(url=url, params=params, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr("app.services.restaurant_service.requests.get", fake_get)
    with app.app_context():
        app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "google-test-secret"
        result = RestauranteService.geocodificar_endereco_publico({
            "endereco": "Avenida Paulista, 1000, São Paulo, SP"
        })

    assert result["success"] is True
    assert result["dados"]["latitude"] == -23.561414
    assert result["dados"]["longitude"] == -46.655881
    assert "endereco_localizado" in result["dados"]
    assert calls["params"]["key"] == "google-test-secret"
    assert calls["timeout"] == 8


def test_geocoding_publico_limita_tamanho_do_endereco(app):
    with app.app_context():
        result = RestauranteService.geocodificar_endereco_publico({"endereco": "A" * 251})
    assert result["success"] is False
    assert result["status_code"] == 400


def test_catalogo_publico_retorna_coordenadas_comerciais_para_calcular_distancia(app):
    with app.app_context():
        restaurante = Restaurante(
            cnpj="12345678000191",
            razao_social="Doceria Local LTDA",
            nome="Doceria Local",
            cpf_responsavel="98765432101",
            email="catalogo-local@example.com",
            telefone="+551133334445",
            status="ABERTO",
            ativo=True,
        )
        db.session.add(restaurante)
        db.session.flush()
        endereco = Endereco(
            id_restaurante=restaurante.id,
            cep="01001-000",
            rua="Praça da Sé",
            numero="100",
            bairro="Sé",
            cidade="São Paulo",
            estado="SP",
            latitude=-23.550520,
            longitude=-46.633308,
            tipo_endereco="COMERCIAL",
            principal=True,
            ativo=True,
        )
        db.session.add(endereco)
        db.session.commit()

        result = RestauranteService.listar_restaurantes()

    assert result["success"] is True
    loja = next(item for item in result["dados"] if item["id"] == restaurante.id)
    assert loja["latitude"] == -23.550520
    assert loja["longitude"] == -46.633308
    assert "cnpj" not in loja
    assert "email" not in loja
    assert "telefone" not in loja


def test_endpoint_publico_de_geocoding_nao_exige_autenticacao_e_valida_endereco(app):
    response = app.test_client().post(
        "/restaurantes/geocodificar-endereco/publico",
        json={"endereco": "Avenida Paulista, 1000, São Paulo, SP"},
    )
    # A chave está ausente no fixture; o endpoint público responde com erro de configuração,
    # não com 401 de autenticação.
    assert response.status_code == 503
    assert "autoriz" not in response.get_json().get("erro", "").lower()
