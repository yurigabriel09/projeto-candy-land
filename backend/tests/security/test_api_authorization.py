from datetime import datetime, timedelta, timezone

import jwt
import pytest
from flask import Flask

from app.database.database import db
from app.models import Categoria, Produto, Restaurante, Usuario
from app.routes.category_routes import categoria_bp
from app.routes.product_routes import produto_bp
from app.routes.restaurant_routes import restaurante_bp
from app.routes.user_routes import user_bp
from app.services.token_service import TokenService


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
    app.register_blueprint(user_bp)
    app.register_blueprint(restaurante_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(categoria_bp)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def _token(tipo_conta, account_id):
    return TokenService.gerar_token(tipo_conta, account_id, f"{tipo_conta.lower()}@example.com")


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _criar_usuario():
    usuario = Usuario(
        nome_completo="Cliente Teste",
        email="cliente@example.com",
        telefone="+5511999991111",
        cpf="12345678901",
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def _criar_restaurante():
    restaurante = Restaurante(
        cnpj="12345678000190",
        razao_social="Doceria Teste LTDA",
        nome="Doceria Teste",
        nome_responsavel="Responsável Particular",
        cpf_responsavel="98765432100",
        email="privado@example.com",
        telefone="+5511888881111",
        descricao="Doces para todos",
        valor_minimo_pedido=10,
        taxa_entrega_base=3,
        taxa_entrega_por_km=1,
        raio_entrega_km=10,
        horario_funcionamento="09:00-18:00",
    )
    db.session.add(restaurante)
    db.session.commit()
    return restaurante


def _criar_produto(restaurante):
    categoria = Categoria(
        id_restaurante=restaurante.id,
        nome="Bolos",
        descricao="Categoria de teste",
    )
    db.session.add(categoria)
    db.session.flush()
    produto = Produto(
        restaurant_id=restaurante.id,
        category_id=categoria.id,
        name="Bolo Teste",
        description="Bolo de teste",
        price=15,
        is_available=True,
        is_imported=False,
        current_stock=7,
        allows_customization=True,
    )
    db.session.add(produto)
    db.session.commit()
    return produto


def test_dados_de_usuario_exigem_token(app):
    response = app.test_client().get("/users/1")
    assert response.status_code == 401


def test_usuario_nao_pode_consultar_dados_de_outro_usuario(app):
    with app.app_context():
        _criar_usuario()
        token = _token("PERSONAL", 999)
        response = app.test_client().get("/users/1", headers=_headers(token))
        assert response.status_code == 403


def test_usuario_pode_consultar_proprios_dados(app):
    with app.app_context():
        usuario = _criar_usuario()
        token = _token("PERSONAL", usuario.id)
        response = app.test_client().get(
            f"/users/{usuario.id}", headers=_headers(token)
        )
        assert response.status_code == 200
        assert response.get_json()["dados"]["email"] == "cliente@example.com"


def test_conta_business_nao_pode_consultar_endpoint_de_usuario(app):
    with app.app_context():
        _criar_usuario()
        token = _token("BUSINESS", 1)
        response = app.test_client().get("/users/1", headers=_headers(token))
        assert response.status_code == 403


def test_listagem_global_de_usuarios_fica_bloqueada_sem_papel_admin(app):
    with app.app_context():
        token = _token("PERSONAL", 1)
        response = app.test_client().get("/users", headers=_headers(token))
        assert response.status_code == 403


def test_atualizacao_de_usuario_exige_token_e_propriedade(app):
    with app.app_context():
        usuario = _criar_usuario()
        client = app.test_client()
        sem_token = client.put(f"/users/{usuario.id}", json={"nome_completo": "Novo"})
        token_outro = _token("PERSONAL", usuario.id + 100)
        outro_usuario = client.put(
            f"/users/{usuario.id}",
            json={"nome_completo": "Novo"},
            headers=_headers(token_outro),
        )
        assert sem_token.status_code == 401
        assert outro_usuario.status_code == 403


def test_exclusao_de_usuario_nao_pode_ser_feita_por_outra_conta(app):
    with app.app_context():
        usuario = _criar_usuario()
        token = _token("PERSONAL", usuario.id + 1)
        response = app.test_client().delete(
            f"/users/{usuario.id}", headers=_headers(token)
        )
        assert response.status_code == 403
        assert db.session.get(Usuario, usuario.id) is not None


def test_mutacoes_de_restaurante_exigem_token_business_e_dono(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        client = app.test_client()
        sem_token = client.put(
            f"/restaurantes/{restaurante.id}", json={"nome": "Alterado"}
        )
        token_personal = _token("PERSONAL", restaurante.id)
        personal = client.put(
            f"/restaurantes/{restaurante.id}",
            json={"nome": "Alterado"},
            headers=_headers(token_personal),
        )
        token_outro = _token("BUSINESS", restaurante.id + 100)
        business_alheio = client.delete(
            f"/restaurantes/{restaurante.id}", headers=_headers(token_outro)
        )
        assert sem_token.status_code == 401
        assert personal.status_code == 403
        assert business_alheio.status_code == 403
        assert db.session.get(Restaurante, restaurante.id).nome == "Doceria Teste"


def test_restaurante_pode_atualizar_apenas_o_proprio_registro(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        token = _token("BUSINESS", restaurante.id)
        response = app.test_client().put(
            f"/restaurantes/{restaurante.id}",
            json={"nome": "Nome Atualizado"},
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert response.get_json()["dados"]["nome"] == "Nome Atualizado"


def test_catalogo_publico_nao_expoe_dados_privados_do_restaurante(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        client = app.test_client()
        respostas = [
            client.get(f"/restaurantes/{restaurante.id}"),
            client.get("/restaurantes"),
        ]
        for response in respostas:
            assert response.status_code == 200
            payload = response.get_json()["dados"]
            dados = payload[0] if isinstance(payload, list) else payload
            assert dados["nome"] == "Doceria Teste"
            assert "cpf_responsavel" not in dados
            assert "email" not in dados
            assert "telefone" not in dados
            assert "cnpj" not in dados
            assert "nome_responsavel" not in dados


def test_categoria_exige_conta_business(app):
    with app.app_context():
        token = _token("PERSONAL", 1)
        response = app.test_client().get("/categorias", headers=_headers(token))
        assert response.status_code == 403


def test_token_assinado_com_claims_invalidos_retorna_401(app):
    with app.app_context():
        token = jwt.encode(
            {
                "sub": "not-an-id",
                "tipo_conta": "PERSONAL",
                "email": "cliente@example.com",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        response = app.test_client().get("/users/1", headers=_headers(token))
        assert response.status_code == 401


def test_cadastro_publico_de_usuario_nao_pula_verificacao_de_identidade(app):
    response = app.test_client().post(
        "/users",
        json={"nome_completo": "Sem verificação", "email": "x@example.com"},
    )
    assert response.status_code == 400


def test_token_sem_expiracao_e_rejeitado(app):
    with app.app_context():
        token = jwt.encode(
            {"sub": "1", "tipo_conta": "PERSONAL", "email": "cliente@example.com"},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        response = app.test_client().get("/users/1", headers=_headers(token))
        assert response.status_code == 401


def test_detalhe_de_produto_exige_token(app):
    response = app.test_client().get("/produtos/1")
    assert response.status_code == 401


def test_cliente_nao_pode_consultar_estoque_interno_de_produto(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        produto = _criar_produto(restaurante)
        token = _token("PERSONAL", 1)
        response = app.test_client().get(
            f"/produtos/{produto.id}", headers=_headers(token)
        )
        assert response.status_code == 403


def test_restaurante_nao_pode_consultar_produto_de_outro_restaurante(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        produto = _criar_produto(restaurante)
        token = _token("BUSINESS", restaurante.id + 100)
        response = app.test_client().get(
            f"/produtos/{produto.id}", headers=_headers(token)
        )
        assert response.status_code == 404


def test_detalhe_interno_de_produto_retorna_estoque_ao_dono(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        produto = _criar_produto(restaurante)
        token = _token("BUSINESS", restaurante.id)
        response = app.test_client().get(
            f"/produtos/{produto.id}", headers=_headers(token)
        )
        assert response.status_code == 200
        assert response.get_json()["produto"]["qtd_estoque"] == 7


def test_catalogos_publicos_nao_expoem_quantidade_exata_do_estoque(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        _criar_produto(restaurante)
        client = app.test_client()
        respostas = [
            client.get("/produtos"),
            client.get(f"/restaurantes/{restaurante.id}/produtos"),
        ]
        for response in respostas:
            assert response.status_code == 200
            body = response.get_json()
            produtos = body.get("produtos", body.get("dados"))
            assert produtos
            assert "qtd_estoque" not in produtos[0]


def test_endpoint_de_gerenciamento_de_estoque_exige_proprietario(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        produto = _criar_produto(restaurante)
        client = app.test_client()
        sem_token = client.get(
            f"/restaurantes/{restaurante.id}/produtos/gerenciamento"
        )
        token_dono = _token("BUSINESS", restaurante.id)
        dono = client.get(
            f"/restaurantes/{restaurante.id}/produtos/gerenciamento",
            headers=_headers(token_dono),
        )
        token_alheio = _token("BUSINESS", restaurante.id + 10)
        alheio = client.get(
            f"/restaurantes/{restaurante.id}/produtos/gerenciamento",
            headers=_headers(token_alheio),
        )
        assert sem_token.status_code == 401
        assert dono.status_code == 200
        assert dono.get_json()["dados"][0]["qtd_estoque"] == 7
        assert alheio.status_code == 403


def test_usuario_nao_pode_alterar_email_sem_fluxo_verificado(app):
    with app.app_context():
        usuario = _criar_usuario()
        token = _token("PERSONAL", usuario.id)
        response = app.test_client().put(
            f"/users/{usuario.id}",
            json={"email": "novo@example.com"},
            headers=_headers(token),
        )
        assert response.status_code == 400
        assert db.session.get(Usuario, usuario.id).email == "cliente@example.com"


def test_restaurante_nao_pode_alterar_email_sem_fluxo_verificado(app):
    with app.app_context():
        restaurante = _criar_restaurante()
        token = _token("BUSINESS", restaurante.id)
        response = app.test_client().put(
            f"/restaurantes/{restaurante.id}",
            json={"email": "novo@example.com"},
            headers=_headers(token),
        )
        assert response.status_code == 400
        assert db.session.get(Restaurante, restaurante.id).email == "privado@example.com"


def test_token_com_tipo_de_conta_malformado_retorna_401(app):
    with app.app_context():
        token = jwt.encode(
            {
                "sub": "1",
                "tipo_conta": ["PERSONAL"],
                "email": "cliente@example.com",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        response = app.test_client().get("/users/1", headers=_headers(token))
        assert response.status_code == 401


def test_token_com_payload_nao_objeto_retorna_401(app, monkeypatch):
    # PyJWT não permite criar um JWT com payload que não seja objeto via jwt.encode.
    # Simulamos um decodificador que devolve payload malformado para testar a
    # proteção defensiva do decorator sem falhar antes de chegar à API.
    monkeypatch.setattr(
        "app.utils.auth_decorator.TokenService.verificar_token",
        lambda _token: ["payload", "nao", "objeto"],
    )
    response = app.test_client().get(
        "/users/1", headers=_headers("token-de-teste")
    )
    assert response.status_code == 401
