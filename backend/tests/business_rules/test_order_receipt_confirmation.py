from decimal import Decimal

import pytest
from flask import Flask

from app.database.database import db
from app.models.address import Endereco
from app.models.category import Categoria
from app.models.item_order import ItemPedido
from app.models.order import Pedido
from app.models.order_receipt_code import OrderReceiptCode
from app.models.product import Produto
from app.models.restaurant import Restaurante
from app.models.user import Usuario
from app.services.order_receipt_service import OrderReceiptService


@pytest.fixture
def app():
    application = Flask("order_receipt_test")
    application.config.update(
        TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False, SECRET_KEY="receipt-test-secret",
    )
    db.init_app(application)
    with application.app_context():
        db.create_all()
        customer = Usuario(nome_completo="Cliente", email="receipt-customer@example.com", telefone="+5511999888777", cpf="12345678901")
        restaurant = Restaurante(cnpj="12345678000190", razao_social="Doceria Teste LTDA", nome="Doceria Teste", cpf_responsavel="98765432100", email="receipt-business@example.com", telefone="+551133334444")
        db.session.add_all([customer, restaurant])
        db.session.flush()
        address = Endereco(id_usuario=customer.id, cep="01001000", rua="Rua Teste", numero="1", bairro="Centro", cidade="São Paulo", estado="SP", tipo_endereco="RESIDENCIAL", principal=True, ativo=True)
        category = Categoria(id_restaurante=restaurant.id, nome="Doces")
        db.session.add_all([address, category])
        db.session.flush()
        product = Produto(restaurant_id=restaurant.id, category_id=category.id, name="Brigadeiro", price=Decimal("10.00"), current_stock=5, is_available=True, is_imported=False, allows_customization=False)
        db.session.add(product)
        db.session.flush()
        order = Pedido(order_code="CL-RECEIPT-1", user_id=customer.id, restaurant_id=restaurant.id, delivery_address_id=address.id, subtotal=Decimal("10.00"), discount=0, delivery_fee=0, platform_fee=0, total=Decimal("10.00"), order_type="PICKUP", status="PRONTO_PARA_ENTREGA", payment_method="PIX")
        db.session.add(order)
        db.session.flush()
        db.session.add(ItemPedido(id_pedido=order.id, id_produto=product.id, quantidade=1, preco_unitario=Decimal("10.00")))
        db.session.commit()
        application.config["TEST_CUSTOMER_ID"] = customer.id
        application.config["TEST_BUSINESS_ID"] = restaurant.id
        application.config["TEST_OTHER_BUSINESS_ID"] = restaurant.id + 50
        application.config["TEST_ORDER_ID"] = order.id
        yield application
        db.session.remove()
        db.engine.dispose()


def test_codigo_recebimento_e_hash_only_e_finaliza_retirada(app):
    with app.app_context():
        customer_id = app.config["TEST_CUSTOMER_ID"]
        business_id = app.config["TEST_BUSINESS_ID"]
        order_id = app.config["TEST_ORDER_ID"]
        issued = OrderReceiptService.emitir_codigo(order_id, customer_id, "PERSONAL")
        assert issued["success"] is True
        code = issued["codigo"]
        record = OrderReceiptCode.query.filter_by(order_id=order_id).one()
        assert record.code_hash != code
        assert OrderReceiptService.emitir_codigo(order_id, customer_id, "PERSONAL")["codigo"] == code

        completed = OrderReceiptService.confirmar_recebimento(order_id, business_id, "BUSINESS", code)
        order = db.session.get(Pedido, order_id)
        assert completed["success"] is True
        assert order.status == "FINALIZADO"
        assert record.used_at is not None
        assert OrderReceiptService.confirmar_recebimento(order_id, business_id, "BUSINESS", code)["success"] is False


def test_codigo_nao_finaliza_pedido_de_outro_restaurante(app):
    with app.app_context():
        issued = OrderReceiptService.emitir_codigo(app.config["TEST_ORDER_ID"], app.config["TEST_CUSTOMER_ID"], "PERSONAL")
        response = OrderReceiptService.confirmar_recebimento(app.config["TEST_ORDER_ID"], app.config["TEST_OTHER_BUSINESS_ID"], "BUSINESS", issued["codigo"])
        assert response["success"] is False
        assert response["status_code"] == 403
        assert db.session.get(Pedido, app.config["TEST_ORDER_ID"]).status == "PRONTO_PARA_ENTREGA"


def test_codigo_incorreto_tem_limite_de_tentativas_e_pode_ser_reemitido(app):
    with app.app_context():
        order_id = app.config["TEST_ORDER_ID"]
        customer_id = app.config["TEST_CUSTOMER_ID"]
        business_id = app.config["TEST_BUSINESS_ID"]
        first = OrderReceiptService.emitir_codigo(order_id, customer_id, "PERSONAL")["codigo"]
        for attempt in range(5):
            failed = OrderReceiptService.confirmar_recebimento(order_id, business_id, "BUSINESS", "999999" if first != "999999" else "000000")
        assert failed["status_code"] == 429
        new_code = OrderReceiptService.emitir_codigo(order_id, customer_id, "PERSONAL")["codigo"]
        assert new_code != first
        assert OrderReceiptService.confirmar_recebimento(order_id, business_id, "BUSINESS", new_code)["success"] is True
