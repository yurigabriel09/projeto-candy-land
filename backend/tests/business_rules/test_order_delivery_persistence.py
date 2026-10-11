import pytest
from flask import Flask

from app.database.database import db
from app.models.delivery import EntregaPedido
from app.models.order import Pedido
from app.routes.order_routes import pedido_bp
from app.services.order_service import OrderService
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
    app.register_blueprint(pedido_bp)

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

        resultado = OrderService.atualizar_status_entrega(
            pedido.id, "PROCURANDO", 1, "BUSINESS"
        )

        assert resultado["success"] is True
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
        assert entrega.status == "PROCURANDO"
        assert entrega.iniciado_em is not None


def test_entrega_concluida_persiste_data_de_entrega(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()
        pedido.status = "PRONTO_PARA_ENTREGA"
        db.session.commit()
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
            resultado = OrderService.atualizar_status_entrega(
                pedido.id, novo_status, 1, "BUSINESS"
            )
            assert resultado["success"] is True

        db.session.refresh(entrega)
        db.session.refresh(pedido)
        assert entrega.status == "ENTREGA_CONCLUIDA"
        assert entrega.concluida_em is not None
        assert pedido.delivered_at is not None
        assert pedido.status == "ENTREGUE"


def test_cancelamento_do_pedido_cancela_entrega(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()

        resultado = OrderService.cancelar_pedido(pedido.id, pedido.user_id)

        assert resultado["success"] is True
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
        assert entrega.status == "CANCELADO"
        assert entrega.cancelada_em is not None


def test_status_entrega_rejeita_cliente_e_restaurante_diferente(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()

        cliente = OrderService.atualizar_status_entrega(
            pedido.id, "PROCURANDO", pedido.user_id, "PERSONAL"
        )
        outro_restaurante = OrderService.atualizar_status_entrega(
            pedido.id, "PROCURANDO", pedido.restaurant_id + 100, "BUSINESS"
        )

        assert cliente["success"] is False
        assert cliente["status_code"] == 403
        assert outro_restaurante["success"] is False
        assert outro_restaurante["status_code"] == 403
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
        db.session.refresh(entrega)
        assert entrega.status == "NAO_SOLICITADO"


def test_endpoint_entrega_exige_token(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()
        response = app.test_client().put(
            f"/pedidos/{pedido.id}/entrega/status", json={"status": "PROCURANDO"}
        )
        assert response.status_code == 401


def test_endpoint_entrega_pode_ser_atualizado_pelo_restaurante_dono(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()
        token = TokenService.gerar_token(
            "BUSINESS", pedido.restaurant_id, "restaurant@example.com"
        )
        response = app.test_client().put(
            f"/pedidos/{pedido.id}/entrega/status",
            json={"status": "PROCURANDO"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["pedido"]["entrega"]["status"] == "PROCURANDO"


def test_endpoint_entrega_rejeita_payload_sem_status(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()
        token = TokenService.gerar_token(
            "BUSINESS", pedido.restaurant_id, "restaurant@example.com"
        )
        response = app.test_client().put(
            f"/pedidos/{pedido.id}/entrega/status",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400


def test_nao_conclui_entrega_se_pedido_nao_pode_ser_entregue(app):
    with app.app_context():
        pedido = criar_pedido_com_entrega()
        for status in (
            "PROCURANDO",
            "MOTORISTA_ENCONTRADO",
            "MOTORISTA_A_CAMINHO",
            "MOTORISTA_NO_RESTAURANTE",
            "PEDIDO_RETIRADO",
            "EM_ROTA",
        ):
            resultado = OrderService.atualizar_status_entrega(
                pedido.id, status, pedido.restaurant_id, "BUSINESS"
            )
            assert resultado["success"] is True

        resultado = OrderService.atualizar_status_entrega(
            pedido.id, "ENTREGA_CONCLUIDA", pedido.restaurant_id, "BUSINESS"
        )
        assert resultado["success"] is False
        assert resultado["status_code"] == 409
        db.session.refresh(pedido)
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
        assert entrega.status == "EM_ROTA"
        assert pedido.status == "PAGAMENTO_CONFIRMADO"
