from datetime import datetime, timedelta

import pytest
from flask import Flask

from app.config.config import telefone_compartilhado_permitido
from app.database.database import db
from app.models import Restaurante, TentativaAutenticacao, Usuario
from app.services.account_identity_service import email_esta_em_uso
from app.services.auth_service import AuthService
from app.services.google_auth_service import GoogleAuthService
from app.services.user_service import UserService
from app.services.restaurant_service import RestauranteService


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="test-secret-key",
        JWT_EXPIRATION_HOURS=1,
        APP_ENV="testing",
        ALLOW_DUPLICATE_PHONE=True,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def _criar_restaurante(email, telefone, cnpj="12345678000199"):
    return Restaurante(
        cnpj=cnpj,
        razao_social="Doceria de Teste LTDA",
        nome="Doceria de Teste",
        cpf_responsavel="12345678901",
        email=email,
        telefone=telefone,
    )


def _criar_tentativa(email, telefone):
    tentativa = TentativaAutenticacao(
        canal_inicial="EMAIL",
        email=email,
        telefone=telefone,
        email_validado=True,
        telefone_validado=True,
        concluida=True,
        expira_em=datetime.now() + timedelta(minutes=10),
    )
    db.session.add(tentativa)
    db.session.commit()
    return tentativa


def test_politica_nao_permite_celular_compartilhado_em_producao():
    assert not telefone_compartilhado_permitido(
        {"APP_ENV": "production", "ALLOW_DUPLICATE_PHONE": "true"}
    )
    assert not telefone_compartilhado_permitido(
        {"APP_ENV": "prod", "ALLOW_DUPLICATE_PHONE": True}
    )
    assert not telefone_compartilhado_permitido(
        {"ALLOW_DUPLICATE_PHONE": "true"}
    )


def test_politica_permite_celular_compartilhado_em_testes_e_desenvolvimento():
    assert telefone_compartilhado_permitido(
        {"APP_ENV": "testing", "ALLOW_DUPLICATE_PHONE": "true"}
    )
    assert telefone_compartilhado_permitido(
        {"APP_ENV": "development", "ALLOW_DUPLICATE_PHONE": True}
    )
    assert not telefone_compartilhado_permitido(
        {"APP_ENV": "development", "ALLOW_DUPLICATE_PHONE": "false"}
    )


def test_email_e_verificado_globalmente_entre_cliente_e_restaurante(app):
    with app.app_context():
        usuario = Usuario(
            nome_completo="Cliente de Teste",
            email="cliente@example.com",
            telefone="+5511999990000",
            cpf="12345678901",
        )
        restaurante = _criar_restaurante(
            "doceria@example.com", "+5511888880000", "12345678000199"
        )
        db.session.add_all([usuario, restaurante])
        db.session.commit()

        assert email_esta_em_uso("CLIENTE@example.com")
        assert email_esta_em_uso("DOCERIA@example.com")
        assert not email_esta_em_uso("novo@example.com")
        assert not email_esta_em_uso(
            "cliente@example.com", usuario_id_ignorar=usuario.id
        )


def test_login_com_celular_compartilhado_resolve_a_conta_pelo_email_verificado(app):
    with app.app_context():
        telefone = "+5511999990000"
        usuario = Usuario(
            nome_completo="Cliente de Teste",
            email="cliente@example.com",
            telefone=telefone,
            cpf="12345678901",
        )
        restaurante = _criar_restaurante(
            "doceria@example.com", telefone, "12345678000199"
        )
        db.session.add_all([usuario, restaurante])
        db.session.commit()

        resultado_cliente = AuthService._finalizar_autenticacao(
            TentativaAutenticacao(email="cliente@example.com", telefone=telefone)
        )
        resultado_restaurante = AuthService._finalizar_autenticacao(
            TentativaAutenticacao(email="doceria@example.com", telefone=telefone)
        )

        assert resultado_cliente["success"] is True
        assert resultado_cliente["dados"]["tipo_conta"] == "PERSONAL"
        assert resultado_cliente["dados"]["id"] == usuario.id
        assert resultado_restaurante["success"] is True
        assert resultado_restaurante["dados"]["tipo_conta"] == "BUSINESS"
        assert resultado_restaurante["dados"]["id"] == restaurante.id


@pytest.mark.parametrize(
    ("ambiente", "deve_criar"),
    [("testing", True), ("production", False)],
)
def test_cadastro_pessoal_com_celular_do_restaurante_respeita_ambiente(
    app, ambiente, deve_criar
):
    with app.app_context():
        telefone = "+5511999990000"
        restaurante = _criar_restaurante(
            "doceria@example.com", telefone, "12345678000199"
        )
        db.session.add(restaurante)
        db.session.commit()

        # Mesmo com a flag true, produção deve sempre desabilitar compartilhamento.
        app.config.update(APP_ENV=ambiente, ALLOW_DUPLICATE_PHONE=True)
        tentativa = _criar_tentativa("novo-cliente@example.com", telefone)

        resultado = UserService.criar_usuario(
            nome_completo="Novo Cliente",
            email="novo-cliente@example.com",
            telefone=telefone,
            cpf="98765432100",
            tentativa_id=tentativa.id,
            endereco={
                "cep": "01001000",
                "rua": "Rua de Teste",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
            },
        )

        assert resultado["success"] is deve_criar, resultado
        if not deve_criar:
            assert resultado["status_code"] == 409
            assert "Telefone já cadastrado" in resultado["erro"]


@pytest.mark.parametrize(
    ("ambiente", "deve_criar"),
    [("testing", True), ("production", False)],
)
def test_cadastro_de_restaurante_com_celular_do_cliente_respeita_ambiente(
    app, ambiente, deve_criar
):
    with app.app_context():
        telefone = "+5511999990000"
        db.session.add(
            Usuario(
                nome_completo="Cliente existente",
                email="cliente-existente@example.com",
                telefone=telefone,
                cpf="12345678901",
            )
        )
        db.session.commit()

        # A flag deve habilitar o compartilhamento nos testes, mas nunca em produção.
        app.config.update(APP_ENV=ambiente, ALLOW_DUPLICATE_PHONE=True)
        tentativa = _criar_tentativa("nova-doceria@example.com", telefone)

        resultado = RestauranteService.criar_restaurante(
            cnpj="98765432000155",
            razao_social="Nova Doceria LTDA",
            nome="Nova Doceria",
            email="nova-doceria@example.com",
            telefone=telefone,
            cpf_responsavel="98765432100",
            tentativa_id=tentativa.id,
            endereco={
                "cep": "01001000",
                "rua": "Rua de Teste",
                "numero": "20",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
            },
        )

        assert resultado["success"] is deve_criar, resultado
        if not deve_criar:
            assert resultado["status_code"] == 409
            assert "telefone já cadastrado" in resultado["erro"].lower()


def test_email_existente_em_restaurante_bloqueia_novo_cadastro_pessoal(app):
    with app.app_context():
        db.session.add(
            _criar_restaurante(
                "doceria@example.com", "+5511888880000", "12345678000199"
            )
        )
        db.session.commit()
        tentativa = _criar_tentativa("DOCERIA@example.com", "+5511999990000")

        resultado = UserService.criar_usuario(
            nome_completo="Tentativa de Cliente",
            email="doceria@example.com",
            telefone="+5511999990000",
            cpf="98765432100",
            tentativa_id=tentativa.id,
            endereco={
                "cep": "01001000",
                "rua": "Rua de Teste",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
            },
        )

        assert resultado["success"] is False
        assert resultado["status_code"] == 409
        assert "e-mail já cadastrado" in resultado["erro"].lower()


def test_oauth_google_permita_celular_existente_somente_em_testes(app, monkeypatch):
    with app.app_context():
        telefone = "+5511999990000"
        db.session.add(
            Usuario(
                nome_completo="Cliente existente",
                email="existente@example.com",
                telefone=telefone,
                cpf="12345678901",
            )
        )
        db.session.commit()

        app.config.update(APP_ENV="testing", ALLOW_DUPLICATE_PHONE=True)
        monkeypatch.setattr(
            GoogleAuthService,
            "validar_credencial",
            staticmethod(lambda credential: {"email": "novo-google@example.com"}),
        )
        monkeypatch.setattr(
            AuthService,
            "_gerar_e_enviar_codigo",
            staticmethod(
                lambda tentativa, canal, destino: {
                    "success": True,
                    "mensagem": "ok",
                }
            ),
        )

        resultado = AuthService.autenticar_google("fake-credential", telefone)

        assert resultado["success"] is True, resultado
        assert resultado["novo_cadastro"] is True
        assert resultado["telefone"] == telefone


def test_oauth_google_nao_contorna_regra_de_celular_em_producao(app, monkeypatch):
    with app.app_context():
        telefone = "+5511999990000"
        db.session.add(
            Usuario(
                nome_completo="Cliente existente",
                email="existente@example.com",
                telefone=telefone,
                cpf="12345678901",
            )
        )
        db.session.commit()

        app.config.update(APP_ENV="production", ALLOW_DUPLICATE_PHONE=True)
        monkeypatch.setattr(
            GoogleAuthService,
            "validar_credencial",
            staticmethod(lambda credential: {"email": "novo-google@example.com"}),
        )

        resultado = AuthService.autenticar_google("fake-credential", telefone)

        assert resultado["success"] is False
        assert resultado["status_code"] == 409
        assert "celular já está vinculado" in resultado["erro"].lower()

def test_oauth_facebook_respeita_regra_de_celular_compartilhado(app, monkeypatch):
    with app.app_context():
        telefone = "+5511999990000"
        db.session.add(
            Usuario(
                nome_completo="Cliente existente",
                email="existente@example.com",
                telefone=telefone,
                cpf="12345678901",
            )
        )
        db.session.commit()

        monkeypatch.setattr(
            AuthService,
            "_gerar_e_enviar_codigo",
            staticmethod(
                lambda tentativa, canal, destino: {
                    "success": True,
                    "mensagem": "ok",
                }
            ),
        )

        app.config.update(APP_ENV="testing", ALLOW_DUPLICATE_PHONE=True)
        resultado_teste = AuthService.autenticar_facebook(
            {"id": "facebook-user-test", "email": "novo-facebook@example.com"},
            telefone,
        )
        assert resultado_teste["success"] is True, resultado_teste

        app.config.update(APP_ENV="production", ALLOW_DUPLICATE_PHONE=True)
        resultado_producao = AuthService.autenticar_facebook(
            {"id": "facebook-user-prod", "email": "outro-facebook@example.com"},
            telefone,
        )
        assert resultado_producao["success"] is False
        assert resultado_producao["status_code"] == 409
        assert "celular já está vinculado" in resultado_producao["erro"].lower()

