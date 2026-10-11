import pytest
from app.database.database import db
from app.models.delivery import EntregaPedido
from app.models.order import Pedido
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
        db.session.remove()
        db.drop_all()
        db.session.remove()


def criar_pedido_com_entrega():
    pedido = Pedido(
        order_code="CL-TESTE001",
        user_id=1,
        restaurant_id=1,
        delivery_address_id=1,
        subtotal=10,
        discount=0,
        delivery_fee=0,
        platform_fee=0,
        total=10,
        order_type="DELIVERY",
        status="PAGAMENTO_CONFIRMADO",
        payment_method="PIX",
    )
    db.session.add(pedido)
    db.session.flush()
    db.session.add(EntregaPedido(pedido_id=pedido.id))
    db.session.commit()
    return pedido


def test_status_da_entrega_e_persistido(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()

        resultado = OrderService.atualizar_status_entrega(pedido.id, "PROCURANDO")

        assert resultado["success"] is True
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
        assert entrega.status == "PROCURANDO"
        assert entrega.iniciado_em is not None


def test_entrega_concluida_persiste_data_de_entrega(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()

        for novo_status in (
            "PROCURANDO",
            "MOTORISTA_ENCONTRADO",
            "MOTORISTA_A_CAMINHO",
            "MOTORISTA_NO_RESTAURANTE",
            "PEDIDO_RETIRADO",
            "EM_ROTA",
            "ENTREGA_CONCLUIDA",
        ):
            resultado = OrderService.atualizar_status_entrega(pedido.id, novo_status)
            assert resultado["success"] is True

        db.session.refresh(entrega)
        db.session.refresh(pedido)
        assert entrega.status == "ENTREGA_CONCLUIDA"
        assert entrega.concluida_em is not None
        assert pedido.delivered_at is not None


def test_cancelamento_do_pedido_cancela_entrega(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()

        resultado = OrderService.cancelar_pedido(pedido.id, pedido.user_id)

        assert resultado["success"] is True
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
        assert entrega.status == "CANCELADO"
        assert entrega.cancelada_em is not None
