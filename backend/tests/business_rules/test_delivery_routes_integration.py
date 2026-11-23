from decimal import Decimal

import pytest
from flask import Flask
from app.database.database import db
from app.models import Categoria, Endereco, EntregaPedido, Pedido, Produto, Restaurante, Usuario
from app.services.order_service import OrderService


@pytest.fixture
def app():
    application = Flask("delivery_routes_integration_test")
    application.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        GOOGLE_MAPS_ROUTES_ENABLED=True,
        GOOGLE_MAPS_ROUTES_API_KEY="routes-test-key",
    )
    db.init_app(application)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def test_rota_billavel_so_e_consultada_na_criacao_valida_do_pedido(app, monkeypatch):
    calls = []

    def fake_route(origin_lat, origin_lng, dest_lat, dest_lng):
        calls.append((origin_lat, origin_lng, dest_lat, dest_lng))
        return {
            "distance_km": 1.25,
            "distance_km_raw": 1.25,
            "duration_seconds": 300,
            "source": "GOOGLE_ROUTES_ESSENTIALS",
        }

    monkeypatch.setattr(
        "app.services.google_routes_service.GoogleRoutesService.calcular_distancia",
        fake_route,
    )

    with app.app_context():
        cliente = Usuario(
            nome_completo="Cliente Rotas", email="rotas-cliente@example.com",
            telefone="11911112222", cpf="11122233344",
        )
        restaurante = Restaurante(
            cnpj="11222333000144", razao_social="Doceria Rotas LTDA",
            nome="Doceria Rotas", cpf_responsavel="22233344455",
            email="rotas-restaurante@example.com", telefone="1133332222",
            taxa_entrega_base=Decimal("3.50"),
            taxa_entrega_por_km=Decimal("2.00"),
            raio_entrega_km=Decimal("20.00"), status="ABERTO",
        )
        db.session.add_all([cliente, restaurante])
        db.session.flush()
        endereco_loja = Endereco(
            id_restaurante=restaurante.id, cep="01001000", rua="Rua A", numero="1",
            bairro="Centro", cidade="São Paulo", estado="SP",
            latitude=Decimal("-23.550520"), longitude=Decimal("-46.633308"),
            tipo_endereco="COMERCIAL", principal=True, ativo=True,
        )
        endereco_cliente = Endereco(
            id_usuario=cliente.id, cep="01001001", rua="Rua B", numero="2",
            bairro="Centro", cidade="São Paulo", estado="SP",
            latitude=Decimal("-23.559520"), longitude=Decimal("-46.633308"),
            tipo_endereco="RESIDENCIAL", principal=True, ativo=True,
        )
        categoria = Categoria(id_restaurante=restaurante.id, nome="Doces")
        db.session.add_all([endereco_loja, endereco_cliente, categoria])
        db.session.flush()
        restaurante.address_id = endereco_loja.id
        produto = Produto(
            restaurant_id=restaurante.id, category_id=categoria.id, name="Brigadeiro",
            price=Decimal("10.00"), is_available=True, current_stock=5,
        )
        db.session.add(produto)
        db.session.commit()

        # O endpoint de estimativa legado continua em linha reta e não consome Routes.
        preview = OrderService.cotar_entrega(
            cliente.id, restaurante.id, "DELIVERY", endereco_cliente.id
        )
        assert preview["success"] is True
        assert calls == []

        result = OrderService.criar_pedido(cliente.id, {
            "restaurant_id": restaurante.id,
            "order_type": "DELIVERY",
            "delivery_address_id": endereco_cliente.id,
            "payment_method": "PIX",
            "items": [{"produto_id": produto.id, "quantidade": 1}],
        })

        assert result["success"] is True, result
        assert len(calls) == 1
        assert result["dados"]["delivery_fee"] == 6.0
        assert result["dados"]["total"] == 16.0
        assert result["dados"]["delivery_distance_km"] == 1.0
        assert result["dados"]["delivery_quote"]["distance_km"] == 1.25
        saved = Pedido.query.one()
        assert saved.delivery_fee == Decimal("6.00")
        assert saved.delivery_distance_km == Decimal("1.00")
        assert EntregaPedido.query.filter_by(pedido_id=saved.id).one()
