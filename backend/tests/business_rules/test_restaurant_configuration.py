import pytest
from flask import Flask

from app.database.database import db
from app.models import Endereco, Restaurante
from app.services.restaurant_service import RestauranteService


@pytest.fixture
def app():
    application = Flask("restaurant_configuration_test")
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="restaurant-config-test-secret",
    )
    db.init_app(application)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.engine.dispose()


def _criar_restaurante():
    restaurante = Restaurante(
        cnpj="12345678000190",
        razao_social="Doceria Teste LTDA",
        nome="Doceria Teste",
        cpf_responsavel="12345678901",
        email="config@example.com",
        telefone="+5511999997777",
    )
    db.session.add(restaurante)
    db.session.commit()
    return restaurante


def _endereco_valido(**alteracoes):
    dados = {
        "cep": "01001-000",
        "rua": "Praça da Sé",
        "numero": "100",
        "complemento": "",
        "bairro": "Sé",
        "cidade": "São Paulo",
        "estado": "SP",
        "referencia": "",
        "latitude": -23.55052,
        "longitude": -46.633308,
    }
    dados.update(alteracoes)
    return dados


def test_configuracao_recupera_endereco_legado_sem_address_id(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        endereco = Endereco(
            id_restaurante=restaurante.id,
            **_endereco_valido(),
            tipo_endereco="COMERCIAL",
            principal=True,
            ativo=True,
        )
        db.session.add(endereco)
        db.session.commit()
        restaurante.address_id = None
        db.session.commit()

        resultado = RestauranteService.buscar_configuracao(restaurante.id)

        assert resultado["success"] is True
        assert resultado["dados"]["endereco"]["cep"] == "01001-000"
        assert resultado["dados"]["endereco"]["rua"] == "Praça da Sé"


def test_atualizar_configuracao_cria_endereco_antes_do_flush(app):
    with app.app_context():
        restaurante = _criar_restaurante()

        resultado = RestauranteService.atualizar_configuracao(
            restaurante.id,
            {"nome": "Doceria Atualizada", "endereco": _endereco_valido()},
        )

        db.session.expire_all()
        restaurante_atualizado = db.session.get(Restaurante, restaurante.id)
        endereco = db.session.get(Endereco, restaurante_atualizado.address_id)

        assert resultado["success"] is True
        assert restaurante_atualizado.nome == "Doceria Atualizada"
        assert endereco is not None
        assert endereco.cep == "01001-000"
        assert float(endereco.latitude) == pytest.approx(-23.55052)
        assert float(endereco.longitude) == pytest.approx(-46.633308)


def test_alterar_endereco_legado_vincula_address_id_e_limpa_coordenadas(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        endereco = Endereco(
            id_restaurante=restaurante.id,
            **_endereco_valido(),
            tipo_endereco="COMERCIAL",
            principal=True,
            ativo=True,
        )
        db.session.add(endereco)
        db.session.commit()
        restaurante.address_id = None
        db.session.commit()

        resultado = RestauranteService.atualizar_configuracao(
            restaurante.id,
            {"endereco": {"cep": "01310-100", "latitude": None, "longitude": None}},
        )

        db.session.expire_all()
        restaurante_atualizado = db.session.get(Restaurante, restaurante.id)
        endereco_atualizado = db.session.get(Endereco, endereco.id)

        assert resultado["success"] is True
        assert restaurante_atualizado.address_id == endereco.id
        assert endereco_atualizado.cep == "01310-100"
        assert endereco_atualizado.latitude is None
        assert endereco_atualizado.longitude is None


def test_endereco_novo_incompleto_retorna_erro_sem_gravar_linha_invalida(app):
    with app.app_context():
        restaurante = _criar_restaurante()

        resultado = RestauranteService.atualizar_configuracao(
            restaurante.id,
            {"endereco": {"cep": "01001-000"}},
        )

        assert resultado["success"] is False
        assert resultado["status_code"] == 400
        assert Endereco.query.filter_by(id_restaurante=restaurante.id).count() == 0
