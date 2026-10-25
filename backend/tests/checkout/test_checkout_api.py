from decimal import Decimal

import pytest
from flask import Flask

from app.database.database import db
from app.models import (
    Categoria,
    Endereco,
    EntregaPedido,
    Pedido,
    Produto,
    Restaurante,
    Usuario,
)
from app.routes.order_routes import pedido_bp
from app.routes.user_routes import user_bp
from app.services.token_service import TokenService


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="checkout-test-secret",
        JWT_EXPIRATION_HOURS=1,
    )
    db.init_app(app)
    app.register_blueprint(user_bp)
    app.register_blueprint(pedido_bp)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def _token(account_type, account_id):
    return TokenService.gerar_token(
        account_type, account_id, f"{account_type.lower()}-{account_id}@example.com"
    )


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _criar_cenario():
    cliente = Usuario(
        nome_completo="Cliente Checkout",
        email="cliente-checkout@example.com",
        telefone="+5511999991234",
        cpf="12345678901",
    )
    outro_cliente = Usuario(
        nome_completo="Outro Cliente",
        email="outro-checkout@example.com",
        telefone="+5511999994321",
        cpf="10987654321",
    )
    restaurante = Restaurante(
        cnpj="12345678000190",
        razao_social="Doceria Checkout LTDA",
        nome="Doceria Checkout",
        cpf_responsavel="98765432100",
        email="restaurante-checkout@example.com",
        telefone="+551133334444",
        taxa_entrega_base=Decimal("3.50"),
        taxa_entrega_por_km=Decimal("2.00"),
        raio_entrega_km=Decimal("20.00"),
    )
    db.session.add_all([cliente, outro_cliente, restaurante])
    db.session.flush()

    endereco_restaurante = Endereco(
        id_restaurante=restaurante.id,
        cep="01001000",
        rua="Praça da Sé",
        numero="100",
        bairro="Sé",
        cidade="São Paulo",
        estado="SP",
        latitude=Decimal("-23.550520"),
        longitude=Decimal("-46.633308"),
        tipo_endereco="COMERCIAL",
        principal=True,
        ativo=True,
    )
    endereco_cliente = Endereco(
        id_usuario=cliente.id,
        cep="01001001",
        rua="Rua de Teste",
        numero="10",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        latitude=Decimal("-23.559520"),
        longitude=Decimal("-46.633308"),
        tipo_endereco="RESIDENCIAL",
        principal=True,
        ativo=True,
    )
    endereco_inativo = Endereco(
        id_usuario=cliente.id,
        cep="01001002",
        rua="Rua Inativa",
        numero="20",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        latitude=Decimal("-23.559520"),
        longitude=Decimal("-46.633308"),
        tipo_endereco="RESIDENCIAL",
        principal=False,
        ativo=False,
    )
    endereco_outro_cliente = Endereco(
        id_usuario=outro_cliente.id,
        cep="01001003",
        rua="Rua de Outra Pessoa",
        numero="30",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        latitude=Decimal("-23.559520"),
        longitude=Decimal("-46.633308"),
        tipo_endereco="RESIDENCIAL",
        principal=True,
        ativo=True,
    )
    categoria = Categoria(id_restaurante=restaurante.id, nome="Doces")
    db.session.add_all(
        [
            endereco_restaurante,
            endereco_cliente,
            endereco_inativo,
            endereco_outro_cliente,
            categoria,
        ]
    )
    db.session.flush()
    restaurante.address_id = endereco_restaurante.id

    produto = Produto(
        restaurant_id=restaurante.id,
        category_id=categoria.id,
        name="Brigadeiro",
        description="Brigadeiro de teste",
        price=Decimal("10.00"),
        is_available=True,
        current_stock=10,
    )
    db.session.add(produto)
    db.session.commit()
    return cliente, outro_cliente, restaurante, endereco_cliente, produto


def test_listagem_de_enderecos_exige_autenticacao_e_titularidade(app):
    with app.app_context():
        cliente, outro_cliente, _, endereco_cliente, _ = _criar_cenario()
        client = app.test_client()

        sem_token = client.get(f"/users/{cliente.id}/enderecos")
        token_outro = client.get(
            f"/users/{cliente.id}/enderecos",
            headers=_headers(_token("PERSONAL", outro_cliente.id)),
        )
        titular = client.get(
            f"/users/{cliente.id}/enderecos",
            headers=_headers(_token("PERSONAL", cliente.id)),
        )

        assert sem_token.status_code == 401
        assert token_outro.status_code == 403
        assert titular.status_code == 200
        dados = titular.get_json()["dados"]
        assert len(dados) == 1
        assert dados[0]["id"] == endereco_cliente.id
        assert dados[0]["principal"] is True


def test_checkout_delivery_cria_pedido_pendente_com_valor_calculado_no_servidor(app):
    with app.app_context():
        cliente, _, restaurante, endereco_cliente, produto = _criar_cenario()
        response = app.test_client().post(
            "/pedidos",
            headers=_headers(_token("PERSONAL", cliente.id)),
            json={
                "restaurant_id": restaurante.id,
                "order_type": "DELIVERY",
                "payment_method": "PIX",
                "delivery_address_id": endereco_cliente.id,
                "items": [{"produto_id": produto.id, "quantidade": 2}],
                # Valores adulterados devem ser ignorados pelo servidor.
                "subtotal": 0,
                "delivery_fee": 0,
                "total": 0,
            },
        )

        assert response.status_code == 201, response.get_json()
        pedido = response.get_json()["pedido"]
        assert pedido["status"] == "PENDENTE_PAGAMENTO"
        assert pedido["order_type"] == "DELIVERY"
        assert pedido["payment_method"] == "PIX"
        assert pedido["subtotal"] == 20.0
        assert pedido["delivery_fee"] == 5.5
        assert pedido["total"] == 25.5
        assert pedido["delivery_address_id"] == endereco_cliente.id
        assert pedido["entrega"]["status"] == "NAO_SOLICITADO"
        assert Pedido.query.count() == 1


def test_checkout_pickup_usa_endereco_do_restaurante_e_taxa_zero(app):
    with app.app_context():
        cliente, _, restaurante, _, produto = _criar_cenario()
        response = app.test_client().post(
            "/pedidos",
            headers=_headers(_token("PERSONAL", cliente.id)),
            json={
                "restaurant_id": restaurante.id,
                "order_type": "PICKUP",
                "payment_method": "CARTAO_CREDITO",
                "items": [{"produto_id": produto.id, "quantidade": 1}],
                "delivery_fee": 999,
            },
        )

        assert response.status_code == 201, response.get_json()
        pedido = response.get_json()["pedido"]
        assert pedido["status"] == "PENDENTE_PAGAMENTO"
        assert pedido["order_type"] == "PICKUP"
        assert pedido["delivery_fee"] == 0.0
        assert pedido["delivery_distance_km"] is None
        assert pedido["delivery_address_id"] is None
        assert pedido["pickup_address_id"] is not None
        assert pedido["entrega"] is None
        assert EntregaPedido.query.count() == 0


def test_checkout_nao_aceita_endereco_de_outro_cliente(app):
    with app.app_context():
        cliente, outro_cliente, restaurante, _, produto = _criar_cenario()
        endereco_alheio = Endereco.query.filter_by(id_usuario=outro_cliente.id).one()
        response = app.test_client().post(
            "/pedidos",
            headers=_headers(_token("PERSONAL", cliente.id)),
            json={
                "restaurant_id": restaurante.id,
                "order_type": "DELIVERY",
                "payment_method": "PIX",
                "delivery_address_id": endereco_alheio.id,
                "items": [{"produto_id": produto.id, "quantidade": 1}],
            },
        )

        assert response.status_code == 400
        assert "não pertence ao cliente" in response.get_json()["erro"]
        assert Pedido.query.count() == 0


def test_conta_restaurante_nao_pode_criar_pedido_de_cliente(app):
    with app.app_context():
        _, _, restaurante, _, produto = _criar_cenario()
        response = app.test_client().post(
            "/pedidos",
            headers=_headers(_token("BUSINESS", restaurante.id)),
            json={
                "restaurant_id": restaurante.id,
                "order_type": "PICKUP",
                "payment_method": "PIX",
                "items": [{"produto_id": produto.id, "quantidade": 1}],
            },
        )
        assert response.status_code == 403
        assert Pedido.query.count() == 0


def test_checkout_rejeita_quantidade_boolean_em_vez_de_inteiro(app):
    with app.app_context():
        cliente, _, restaurante, endereco_cliente, produto = _criar_cenario()
        response = app.test_client().post(
            "/pedidos",
            headers=_headers(_token("PERSONAL", cliente.id)),
            json={
                "restaurant_id": restaurante.id,
                "order_type": "DELIVERY",
                "payment_method": "PIX",
                "delivery_address_id": endereco_cliente.id,
                "items": [{"produto_id": produto.id, "quantidade": True}],
            },
        )
        assert response.status_code == 400
        assert "devem ser inteiros" in response.get_json()["erro"]
        assert Pedido.query.count() == 0


def test_checkout_rejeita_corpo_json_que_nao_e_objeto(app):
    with app.app_context():
        cliente, _, _, _, _ = _criar_cenario()
        response = app.test_client().post(
            "/pedidos",
            headers=_headers(_token("PERSONAL", cliente.id)),
            json=["payload", "nao", "objeto"],
        )
        assert response.status_code == 400
        assert "objeto JSON" in response.get_json()["erro"]
        assert Pedido.query.count() == 0
