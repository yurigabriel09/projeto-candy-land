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
from app.services.order_service import ORDER_TYPES, OrderService


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


def test_tipos_de_pedido_suportados():
    assert ORDER_TYPES == {"DELIVERY", "PICKUP"}
    OrderService._validate_order_type("DELIVERY")
    OrderService._validate_order_type("PICKUP")


def test_tipo_de_pedido_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="DELIVERY ou PICKUP"):
        OrderService._validate_order_type("BALCAO")


def test_pedido_para_retirada_usa_endereco_do_restaurante_e_nao_cria_entrega(app):
    with app.app_context():
        cliente = Usuario(
            nome_completo="Cliente de teste",
            email="cliente-teste@example.com",
            telefone="11999990000",
            cpf="12345678901",
        )
        restaurante = Restaurante(
            cnpj="12345678000199",
            razao_social="Doceria Teste LTDA",
            nome="Doceria Teste",
            cpf_responsavel="12345678901",
            email="doceria-teste@example.com",
            telefone="1133334444",
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
            tipo_endereco="COMERCIAL",
            principal=True,
            ativo=True,
        )
        categoria = Categoria(id_restaurante=restaurante.id, nome="Doces")
        db.session.add_all([endereco_restaurante, categoria])
        db.session.flush()
        restaurante.address_id = endereco_restaurante.id

        produto = Produto(
            restaurant_id=restaurante.id,
            category_id=categoria.id,
            name="Brigadeiro",
            price=5.00,
            is_available=True,
            current_stock=20,
        )
        db.session.add(produto)
        db.session.commit()

        resultado = OrderService.criar_pedido(
            cliente.id,
            {
                "restaurant_id": restaurante.id,
                "order_type": "PICKUP",
                "payment_method": "PIX",
                "delivery_fee": 99.90,
                "items": [{"produto_id": produto.id, "quantidade": 2}],
            },
        )

        assert resultado["success"] is True, resultado
        pedido = Pedido.query.filter_by(
            order_code=resultado["dados"]["order_code"]
        ).one()
        assert pedido.order_type == "PICKUP"
        assert float(pedido.delivery_fee) == 0
        assert pedido.delivery_address_id == endereco_restaurante.id
        assert resultado["dados"]["delivery_address_id"] is None
        assert resultado["dados"]["pickup_address_id"] == endereco_restaurante.id
        assert EntregaPedido.query.filter_by(pedido_id=pedido.id).first() is None


def test_retirada_e_rejeitada_se_restaurante_nao_tem_endereco_ativo(app):
    with app.app_context():
        restaurante = Restaurante(
            cnpj="98765432000199",
            razao_social="Sem Endereço LTDA",
            nome="Doceria sem endereço",
            cpf_responsavel="10987654321",
            email="sem-endereco@example.com",
            telefone="1132221111",
        )
        db.session.add(restaurante)
        db.session.commit()

        with pytest.raises(ValueError, match="endereço ativo cadastrado"):
            OrderService._resolve_pickup_address(restaurante.id)
