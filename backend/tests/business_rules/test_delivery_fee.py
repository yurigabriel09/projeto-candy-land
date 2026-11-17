from decimal import Decimal

import pytest
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
from app.services.order_service import OrderService
from flask import Flask


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        # Cada fixture usa SQLite em memória e uma app exclusiva; descartar o engine
        # é suficiente e evita warnings ao tentar dropar FKs cíclicas (SQLite não ALTER).
        db.session.remove()
        db.engine.dispose()


def seed_delivery_scenario():
    customer = Usuario(
        nome_completo="Cliente Taxa",
        email="taxa-cliente@example.com",
        telefone="11911112222",
        cpf="11122233344",
    )
    restaurant = Restaurante(
        cnpj="11222333000144",
        razao_social="Doceria Distância LTDA",
        nome="Doceria Distância",
        cpf_responsavel="22233344455",
        email="taxa-restaurante@example.com",
        telefone="1133332222",
        taxa_entrega_base=Decimal("3.50"),
        taxa_entrega_por_km=Decimal("2.00"),
        raio_entrega_km=Decimal("20.00"),
        status="ABERTO",
    )
    db.session.add_all([customer, restaurant])
    db.session.flush()

    restaurant_address = Endereco(
        id_restaurante=restaurant.id, cep="01001000", rua="Rua A", numero="1",
        bairro="Centro", cidade="São Paulo", estado="SP",
        latitude=Decimal("-23.550520"), longitude=Decimal("-46.633308"),
        tipo_endereco="COMERCIAL", principal=True, ativo=True,
    )
    customer_address = Endereco(
        id_usuario=customer.id, cep="01001001", rua="Rua B", numero="2",
        bairro="Centro", cidade="São Paulo", estado="SP",
        latitude=Decimal("-23.559520"), longitude=Decimal("-46.633308"),
        tipo_endereco="RESIDENCIAL", principal=True, ativo=True,
    )
    category = Categoria(id_restaurante=restaurant.id, nome="Doces")
    db.session.add_all([restaurant_address, customer_address, category])
    db.session.flush()
    restaurant.address_id = restaurant_address.id
    product = Produto(
        restaurant_id=restaurant.id, category_id=category.id, name="Brigadeiro",
        price=Decimal("10.00"), is_available=True, current_stock=15,
    )
    db.session.add(product)
    db.session.commit()
    return customer, restaurant, customer_address, product


def test_taxa_e_calculada_no_servidor_e_ignora_valor_enviado_pelo_cliente(app):
    with app.app_context():
        customer, restaurant, address, product = seed_delivery_scenario()
        result = OrderService.criar_pedido(
            customer.id,
            {
                "restaurant_id": restaurant.id,
                "order_type": "DELIVERY",
                "delivery_address_id": address.id,
                "payment_method": "PIX",
                "delivery_fee": 0,  # Tentativa do cliente de zerar a taxa é ignorada.
                "discount": 10,  # Não há promoção validada no backend; desconto é ignorado.
                "platform_fee": 50,  # Taxa de plataforma não pode ser imposta pelo cliente.
                "items": [{"produto_id": product.id, "quantidade": 1}],
            },
        )

        assert result["success"] is True, result
        order = Pedido.query.filter_by(id=result["dados"]["id"]).one()
        assert order.delivery_distance_km == Decimal("1.00")
        assert order.delivery_fee == Decimal("5.50")
        assert order.total == Decimal("15.50")
        assert EntregaPedido.query.filter_by(pedido_id=order.id).one()

def test_entrega_fora_do_raio_e_rejeitada(app):
    with app.app_context():
        customer, restaurant, address, product = seed_delivery_scenario()
        address.latitude = Decimal("-23.850000")
        db.session.commit()

        result = OrderService.criar_pedido(
            customer.id,
            {
                "restaurant_id": restaurant.id,
                "order_type": "DELIVERY",
                "delivery_address_id": address.id,
                "payment_method": "PIX",
                "items": [{"produto_id": product.id, "quantidade": 1}],
            },
        )

        assert result["success"] is False
        assert result["status_code"] == 400
        assert "fora do raio" in result["erro"]
        assert Pedido.query.count() == 0

def test_entrega_geocodifica_automaticamente_enderecos_sem_coordenadas(app, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "OK",
                "results": [{
                    "formatted_address": "Rua B, 2, São Paulo - SP, Brasil",
                    "geometry": {"location": {"lat": -23.559520, "lng": -46.633308}},
                }],
            }

    calls = []

    def fake_get(url, params, timeout):
        address_text = params["address"]
        calls.append(address_text)
        response = FakeResponse()
        if "Rua A" in address_text:
            response.json = lambda: {
                "status": "OK",
                "results": [{
                    "formatted_address": "Rua A, 1, São Paulo - SP, Brasil",
                    "geometry": {"location": {"lat": -23.550520, "lng": -46.633308}},
                }],
            }
        else:
            response.json = lambda: {
                "status": "OK",
                "results": [{
                    "formatted_address": "Rua B, 2, São Paulo - SP, Brasil",
                    "geometry": {"location": {"lat": -23.559520, "lng": -46.633308}},
                }],
            }
        return response

    monkeypatch.setattr("app.services.geocoding_service.requests.get", fake_get)
    with app.app_context():
        app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "google-test-key"
        customer, restaurant, address, product = seed_delivery_scenario()
        address.latitude = None
        address.longitude = None
        restaurant_address = Endereco.query.filter_by(id=restaurant.address_id).one()
        restaurant_address.latitude = None
        restaurant_address.longitude = None
        db.session.commit()

        result = OrderService.criar_pedido(
            customer.id,
            {
                "restaurant_id": restaurant.id,
                "order_type": "DELIVERY",
                "delivery_address_id": address.id,
                "payment_method": "PIX",
                "items": [{"produto_id": product.id, "quantidade": 1}],
            },
        )

        assert result["success"] is True, result
        assert len(calls) == 2
        assert address.latitude == Decimal("-23.559520")
        assert restaurant_address.latitude == Decimal("-23.550520")
        order = Pedido.query.one()
        assert order.delivery_distance_km == Decimal("1.00")
        assert order.delivery_fee == Decimal("5.50")
        assert Pedido.query.count() == 1

def test_raio_precisa_estar_configurado_para_delivery(app):
    with app.app_context():
        customer, restaurant, address, product = seed_delivery_scenario()
        restaurant.raio_entrega_km = None
        db.session.commit()
        result = OrderService.criar_pedido(
            customer.id,
            {
                "restaurant_id": restaurant.id,
                "order_type": "DELIVERY",
                "delivery_address_id": address.id,
                "payment_method": "PIX",
                "items": [{"produto_id": product.id, "quantidade": 1}],
            },
        )
        assert result["success"] is False
        assert "raio máximo" in result["erro"]


def test_migracao_de_taxa_e_idempotente_para_banco_existente(app):
    from app.database.migrations import migrar_taxa_entrega_por_distancia
    from sqlalchemy import create_engine, text

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE restaurants (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE orders (id INTEGER PRIMARY KEY)"))

    first = migrar_taxa_entrega_por_distancia(engine)
    second = migrar_taxa_entrega_por_distancia(engine)
    assert set(first) == {"restaurants.taxa_entrega_por_km", "orders.delivery_distance_km"}
    assert second == []
    engine.dispose()
