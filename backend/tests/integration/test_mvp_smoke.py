"""Testes de fumaça integrados para o caminho principal do CandyLand MVP.

O teste usa uma base SQLite em memória e um JWT de teste já autenticado. Ele
valida os contratos reais das rotas, sem depender de Twilio, Google ou Facebook.
"""
from decimal import Decimal

import pytest
from flask import Flask

from app.database.database import db
from app.models import Categoria, Endereco, Pedido, Produto, Restaurante, Usuario
from app.routes.order_routes import pedido_bp
from app.routes.product_routes import produto_bp
from app.routes.restaurant_routes import restaurante_bp
from app.routes.user_routes import user_bp
from app.services.token_service import TokenService



@pytest.fixture
def app():
    application = Flask("mvp_smoke_test")
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="mvp-smoke-test-secret",
        JWT_EXPIRATION_HOURS=1,
    )
    db.init_app(application)
    application.register_blueprint(user_bp)
    application.register_blueprint(restaurante_bp)
    application.register_blueprint(produto_bp)
    application.register_blueprint(pedido_bp)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.engine.dispose()


def _token(tipo_conta, account_id, email):
    return TokenService.gerar_token(tipo_conta, account_id, email)


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _preparar_cenario():
    cliente = Usuario(
        nome_completo="Cliente Smoke Test",
        email="cliente-smoke@example.com",
        telefone="+5511999911000",
        cpf="12345678901",
    )
    restaurante = Restaurante(
        cnpj="12345678000191",
        razao_social="Doceria Smoke Test LTDA",
        nome="Doceria Smoke Test",
        cpf_responsavel="98765432100",
        email="doceria-smoke@example.com",
        telefone="+551133331000",
        descricao="Restaurante usado nos testes de integração.",
        taxa_entrega_base=Decimal("3.50"),
        taxa_entrega_por_km=Decimal("2.00"),
        raio_entrega_km=Decimal("20.00"),
        status="ABERTO",
        ativo=True,
    )
    db.session.add_all([cliente, restaurante])
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
        rua="Rua do Cliente",
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
    categoria = Categoria(id_restaurante=restaurante.id, nome="Doces")
    db.session.add_all([endereco_restaurante, endereco_cliente, categoria])
    db.session.flush()
    restaurante.address_id = endereco_restaurante.id

    produto = Produto(
        restaurant_id=restaurante.id,
        category_id=categoria.id,
        name="Brigadeiro Smoke Test",
        description="Produto fictício para teste integrado.",
        price=Decimal("10.00"),
        is_available=True,
        is_imported=False,
        current_stock=10,
        allows_customization=False,
    )
    db.session.add(produto)
    db.session.commit()

    return cliente, restaurante, endereco_cliente, produto


def test_smoke_cliente_catalogo_endereco_checkout_e_consulta_pedido(app):
    """Percorre catálogo público → endereço autenticado → pedido → consulta."""
    with app.app_context():
        cliente, restaurante, endereco_cliente, produto = _preparar_cenario()
        token_cliente = _token("PERSONAL", cliente.id, cliente.email)
        client = app.test_client()

        # 1. O cliente consegue descobrir o restaurante pelo catálogo público.
        restaurantes_response = client.get("/restaurantes")
        assert restaurantes_response.status_code == 200
        restaurantes = restaurantes_response.get_json()["dados"]
        restaurante_publico = next(
            (item for item in restaurantes if item["id"] == restaurante.id), None
        )
        assert restaurante_publico is not None
        assert restaurante_publico["nome"] == restaurante.nome
        assert "email" not in restaurante_publico
        assert "telefone" not in restaurante_publico
        assert "cnpj" not in restaurante_publico

        # 2. O produto é encontrado no catálogo sem expor estoque interno.
        produtos_response = client.get(
            f"/restaurantes/{restaurante.id}/produtos"
        )
        assert produtos_response.status_code == 200
        produtos_publicos = produtos_response.get_json()["dados"]
        produto_publico = next(
            (item for item in produtos_publicos if item["id_produto"] == produto.id),
            None,
        )
        assert produto_publico is not None
        assert produto_publico["nome_produto"] == produto.name
        assert produto_publico["preco_produto"] == 10.0
        assert "qtd_estoque" not in produto_publico
        assert "current_stock" not in produto_publico

        # 3. Endereços só podem ser consultados pelo cliente autenticado titular.
        enderecos_response = client.get(
            f"/users/{cliente.id}/enderecos", headers=_headers(token_cliente)
        )
        assert enderecos_response.status_code == 200
        enderecos = enderecos_response.get_json()["dados"]
        assert len(enderecos) == 1
        assert enderecos[0]["id"] == endereco_cliente.id
        assert enderecos[0]["ativo"] is True

        # 4. O checkout ignora valores monetários enviados pelo cliente e cria
        #    o pedido pendente a partir dos itens e dos dados persistidos.
        criar_pedido_response = client.post(
            "/pedidos",
            headers=_headers(token_cliente),
            json={
                "restaurant_id": restaurante.id,
                "order_type": "DELIVERY",
                "payment_method": "PIX",
                "delivery_address_id": endereco_cliente.id,
                "items": [{"produto_id": produto.id, "quantidade": 2}],
                "subtotal": 0,
                "delivery_fee": 0,
                "total": 0,
            },
        )
        assert criar_pedido_response.status_code == 201, criar_pedido_response.get_json()
        pedido_criado = criar_pedido_response.get_json()["pedido"]
        assert pedido_criado["status"] == "PENDENTE_PAGAMENTO"
        assert pedido_criado["order_type"] == "DELIVERY"
        assert pedido_criado["subtotal"] == 20.0
        assert pedido_criado["delivery_fee"] > 0
        assert pedido_criado["total"] == pytest.approx(
            pedido_criado["subtotal"] + pedido_criado["delivery_fee"]
        )
        assert pedido_criado["delivery_address_id"] == endereco_cliente.id

        # 5. O pedido recém-criado aparece na consulta do próprio cliente.
        pedido_id = pedido_criado["id"]
        detalhe_response = client.get(
            f"/pedidos/{pedido_id}", headers=_headers(token_cliente)
        )
        assert detalhe_response.status_code == 200
        pedido_detalhe = detalhe_response.get_json()["pedido"]
        assert pedido_detalhe["order_code"] == pedido_criado["order_code"]
        assert pedido_detalhe["status"] == "PENDENTE_PAGAMENTO"
        assert len(pedido_detalhe["items"]) == 1
        assert pedido_detalhe["items"][0]["produto_id"] == produto.id
        assert pedido_detalhe["items"][0]["quantidade"] == 2

        listagem_response = client.get("/pedidos", headers=_headers(token_cliente))
        assert listagem_response.status_code == 200
        ids_pedidos = [item["id"] for item in listagem_response.get_json()["pedidos"]]
        assert pedido_id in ids_pedidos

        # Pedido pendente não deve dar baixa de estoque antes da confirmação de pagamento.
        db.session.refresh(produto)
        assert produto.current_stock == 10
        assert Pedido.query.filter_by(id=pedido_id).count() == 1


def test_smoke_checkout_retirada_nao_cria_entrega_logistica(app):
    """Confirma o caminho alternativo PICKUP pelo mesmo contrato da API."""
    with app.app_context():
        cliente, restaurante, _endereco_cliente, produto = _preparar_cenario()
        token_cliente = _token("PERSONAL", cliente.id, cliente.email)
        response = app.test_client().post(
            "/pedidos",
            headers=_headers(token_cliente),
            json={
                "restaurant_id": restaurante.id,
                "order_type": "PICKUP",
                "payment_method": "CARTAO_CREDITO",
                "items": [{"produto_id": produto.id, "quantidade": 1}],
                "delivery_fee": 500,
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


def test_smoke_nao_autentica_nao_consegue_criar_pedido(app):
    with app.app_context():
        _cliente, restaurante, endereco_cliente, produto = _preparar_cenario()
        response = app.test_client().post(
            "/pedidos",
            json={
                "restaurant_id": restaurante.id,
                "order_type": "DELIVERY",
                "payment_method": "PIX",
                "delivery_address_id": endereco_cliente.id,
                "items": [{"produto_id": produto.id, "quantidade": 1}],
            },
        )
        assert response.status_code == 401
        assert Pedido.query.count() == 0
