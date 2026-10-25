from decimal import Decimal

import pytest
from flask import Flask

from app.database.database import db
from app.models import (
    Categoria,
    Endereco,
    ItemPedido,
    Pedido,
    PaymentAttempt,
    Produto,
    Restaurante,
    Usuario,
)
from app.routes.order_routes import pedido_bp
from app.services.payment_providers.contracts import UnsupportedPaymentProvider
from app.services.payment_providers.factory import get_payment_provider
from app.services.token_service import TokenService


@pytest.fixture
def app():
    application = Flask(__name__)
    application.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="mock-payment-test-secret",
        JWT_EXPIRATION_HOURS=1,
        APP_ENV="testing",
        PAYMENT_PROVIDER="mock",
    )
    db.init_app(application)
    application.register_blueprint(pedido_bp)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.engine.dispose()


def _token(account_type, account_id):
    return TokenService.gerar_token(
        account_type,
        account_id,
        f"{account_type.lower()}-{account_id}@example.com",
    )


def _headers(account_type, account_id):
    return {"Authorization": f"Bearer {_token(account_type, account_id)}"}


def _create_order(stock=10, quantity=2):
    customer = Usuario(
        nome_completo="Cliente Mock",
        email="cliente-mock@example.com",
        telefone="+5511999000101",
        cpf="12345678901",
    )
    other_customer = Usuario(
        nome_completo="Outro Cliente Mock",
        email="outro-cliente-mock@example.com",
        telefone="+5511999000102",
        cpf="12345678902",
    )
    restaurant = Restaurante(
        cnpj="12345678000190",
        razao_social="Doceria Mock LTDA",
        nome="Doceria Mock",
        cpf_responsavel="98765432100",
        email="doceria-mock@example.com",
        telefone="+551133334455",
        taxa_entrega_base=0,
        taxa_entrega_por_km=0,
        raio_entrega_km=10,
    )
    db.session.add_all([customer, other_customer, restaurant])
    db.session.flush()

    address = Endereco(
        id_usuario=customer.id,
        cep="01001000",
        rua="Rua Mock",
        numero="10",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        tipo_endereco="RESIDENCIAL",
        principal=True,
        ativo=True,
    )
    category = Categoria(id_restaurante=restaurant.id, nome="Doces Mock")
    db.session.add_all([address, category])
    db.session.flush()

    product = Produto(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Brigadeiro Mock",
        description="Item de teste",
        price=Decimal("10.00"),
        is_available=True,
        is_imported=False,
        current_stock=stock,
        allows_customization=False,
    )
    db.session.add(product)
    db.session.flush()

    order = Pedido(
        order_code=f"CL-MOCK-{customer.id:04d}",
        user_id=customer.id,
        restaurant_id=restaurant.id,
        delivery_address_id=address.id,
        subtotal=Decimal("10.00") * quantity,
        discount=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        platform_fee=Decimal("0.00"),
        total=Decimal("10.00") * quantity,
        order_type="PICKUP",
        status="PENDENTE_PAGAMENTO",
        payment_method="PIX",
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(
        ItemPedido(
            id_pedido=order.id,
            id_produto=product.id,
            quantidade=quantity,
            preco_unitario=Decimal("10.00"),
        )
    )
    db.session.commit()
    return customer, other_customer, order, product


def test_criacao_de_pagamento_usa_total_do_backend_e_e_idempotente(app):
    with app.app_context():
        customer, _, order, _ = _create_order()
        client = app.test_client()
        headers = {
            **_headers("PERSONAL", customer.id),
            "Idempotency-Key": "test-order-payment-1",
        }

        first = client.post(
            f"/pedidos/{order.id}/pagamento", headers=headers, json={"amount": 0.01}
        )
        second = client.post(
            f"/pedidos/{order.id}/pagamento", headers=headers, json={"amount": 999999}
        )

        assert first.status_code == 201
        assert second.status_code == 200
        first_payment = first.get_json()["pagamento"]
        second_payment = second.get_json()["pagamento"]
        assert first_payment["amount"] == 20.0
        assert first_payment["status"] == "PENDING"
        assert first_payment["provider"] == "mock"
        assert first_payment["id"] == second_payment["id"]
        assert PaymentAttempt.query.count() == 1


def test_aprovacao_simulada_confirma_pedido_e_debita_estoque_uma_vez(app):
    with app.app_context():
        customer, _, order, product = _create_order(stock=10, quantity=2)
        client = app.test_client()
        headers = _headers("PERSONAL", customer.id)

        created = client.post(f"/pedidos/{order.id}/pagamento", headers=headers)
        assert created.status_code == 201

        first = client.post(
            f"/pedidos/{order.id}/pagamento/mock-result",
            headers=headers,
            json={"outcome": "approved", "amount": 0.01},
        )
        db.session.refresh(order)
        db.session.refresh(product)
        assert first.status_code == 200
        assert first.get_json()["pagamento"]["status"] == "APPROVED"
        assert order.status == "PAGAMENTO_CONFIRMADO"
        assert product.current_stock == 8

        repeated = client.post(
            f"/pedidos/{order.id}/pagamento/mock-result",
            headers=headers,
            json={"outcome": "approved"},
        )
        db.session.refresh(product)
        assert repeated.status_code == 200
        assert product.current_stock == 8


def test_recusa_simulada_nao_confirma_pedido_nem_altera_estoque(app):
    with app.app_context():
        customer, _, order, product = _create_order(stock=10, quantity=2)
        client = app.test_client()
        headers = _headers("PERSONAL", customer.id)
        assert client.post(f"/pedidos/{order.id}/pagamento", headers=headers).status_code == 201

        response = client.post(
            f"/pedidos/{order.id}/pagamento/mock-result",
            headers=headers,
            json={"outcome": "rejected"},
        )
        db.session.refresh(order)
        db.session.refresh(product)
        assert response.status_code == 200
        assert response.get_json()["pagamento"]["status"] == "REJECTED"
        assert order.status == "PENDENTE_PAGAMENTO"
        assert product.current_stock == 10


def test_cliente_nao_pode_iniciar_ou_simular_pagamento_de_outro_cliente(app):
    with app.app_context():
        customer, other_customer, order, _ = _create_order()
        client = app.test_client()

        create = client.post(
            f"/pedidos/{order.id}/pagamento",
            headers=_headers("PERSONAL", other_customer.id),
        )
        simulate = client.post(
            f"/pedidos/{order.id}/pagamento/mock-result",
            headers=_headers("PERSONAL", other_customer.id),
            json={"outcome": "approved"},
        )
        assert create.status_code == 403
        assert simulate.status_code == 403
        assert PaymentAttempt.query.count() == 0


def test_mock_falha_fechada_em_producao(app):
    with app.app_context():
        customer, _, order, _ = _create_order()
        app.config["APP_ENV"] = "production"
        response = app.test_client().post(
            f"/pedidos/{order.id}/pagamento",
            headers=_headers("PERSONAL", customer.id),
        )
        assert response.status_code == 403
        with pytest.raises(UnsupportedPaymentProvider, match="apenas em desenvolvimento/testes"):
            get_payment_provider(config={"APP_ENV": "production", "PAYMENT_PROVIDER": "mock"})


def test_estoque_insuficiente_nao_confirma_pedido_e_exige_revisao(app):
    with app.app_context():
        customer, _, order, product = _create_order(stock=1, quantity=2)
        client = app.test_client()
        headers = _headers("PERSONAL", customer.id)
        assert client.post(f"/pedidos/{order.id}/pagamento", headers=headers).status_code == 201

        response = client.post(
            f"/pedidos/{order.id}/pagamento/mock-result",
            headers=headers,
            json={"outcome": "approved"},
        )
        db.session.refresh(order)
        db.session.refresh(product)
        attempt = PaymentAttempt.query.filter_by(order_id=order.id).first()
        assert response.status_code == 409
        assert order.status == "PENDENTE_PAGAMENTO"
        assert product.current_stock == 1
        assert attempt.status == "ACTION_REQUIRED"
