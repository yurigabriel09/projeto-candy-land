from decimal import Decimal

import pytest
from flask import Flask

from app.database.database import db
from app.models import Endereco, Pedido, PaymentAttempt, Restaurante, Usuario
from app.services import payment_service as payment_service_module
from app.services.payment_providers.contracts import PaymentMethod, PaymentResult, PaymentStatus
from app.services.payment_service import PaymentService


@pytest.fixture
def app():
    application = Flask(__name__)
    application.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="payment-dispatch-test-secret",
        APP_ENV="testing",
        PAYMENT_PROVIDER="auto",
    )
    db.init_app(application)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.engine.dispose()


def _order(method):
    customer = Usuario(
        nome_completo="Cliente Dispatch",
        email="cliente-dispatch@example.com",
        telefone="+5511999000301",
        cpf="12345678901",
    )
    restaurant = Restaurante(
        cnpj="12345678000190",
        razao_social="Doceria Dispatch LTDA",
        nome="Doceria Dispatch",
        cpf_responsavel="98765432100",
        email="dispatch@example.com",
        telefone="+551133334457",
        taxa_entrega_base=0,
        taxa_entrega_por_km=0,
        raio_entrega_km=10,
    )
    db.session.add_all([customer, restaurant])
    db.session.flush()
    address = Endereco(
        id_usuario=customer.id,
        cep="01001000",
        rua="Rua Dispatch",
        numero="1",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        tipo_endereco="RESIDENCIAL",
        principal=True,
        ativo=True,
    )
    db.session.add(address)
    db.session.flush()
    order = Pedido(
        order_code=f"CL-DISP-{customer.id:04d}",
        user_id=customer.id,
        restaurant_id=restaurant.id,
        delivery_address_id=address.id,
        subtotal=Decimal("35.90"),
        discount=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        platform_fee=Decimal("0.00"),
        total=Decimal("35.90"),
        order_type="PICKUP",
        status="PENDENTE_PAGAMENTO",
        payment_method=method,
    )
    db.session.add(order)
    db.session.commit()
    return customer, order


@pytest.mark.parametrize(
    ("selected_method", "expected_provider", "expected_rail"),
    [
        ("PIX", "mercadopago", PaymentMethod.PIX),
        ("PAYPAL", "paypal", PaymentMethod.CARD),
        ("MERCADO_PAGO", "mercadopago", PaymentMethod.CARD),
    ],
)
def test_checkout_despacha_para_o_provedor_escolhido_e_usa_total_persistido(
    app, monkeypatch, selected_method, expected_provider, expected_rail
):
    with app.app_context():
        customer, order = _order(selected_method)
        selected = []

        class FakeProvider:
            provider_name = expected_provider

            def validar_metodo(self, method):
                assert method is expected_rail

            def create_payment(self, command):
                assert command.order_id == str(order.id)
                assert command.amount == Decimal("35.90")
                assert command.currency == "BRL"
                assert command.method is expected_rail
                assert command.payer_email == customer.email
                selected.append(self.provider_name)
                return PaymentResult(
                    provider=self.provider_name,
                    provider_payment_id=f"{self.provider_name}-{order.id}",
                    status=PaymentStatus.PENDING,
                    amount=command.amount,
                    currency="BRL",
                    approval_url="https://checkout.example.test/approval" if expected_provider == "paypal" or selected_method == "MERCADO_PAGO" else None,
                    pix_copy_paste="000201-fake-code" if expected_rail is PaymentMethod.PIX else None,
                    pix_qr_code_base64="ZmFrZS1xci1jb2Rl" if expected_rail is PaymentMethod.PIX else None,
                )

        monkeypatch.setattr(payment_service_module, "get_payment_provider", lambda provider_name=None: (selected.append(provider_name), FakeProvider())[1])
        result = PaymentService.criar_pagamento(order.id, customer.id, "PERSONAL")

        assert result["success"] is True
        assert selected == [expected_provider, expected_provider]
        attempt = PaymentAttempt.query.filter_by(order_id=order.id).one()
        assert attempt.provider == expected_provider
        assert attempt.payment_method == selected_method
        assert attempt.amount == Decimal("35.90")
