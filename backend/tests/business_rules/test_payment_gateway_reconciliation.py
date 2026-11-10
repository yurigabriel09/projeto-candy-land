from decimal import Decimal

import pytest
from flask import Flask

from app.database.database import db
from app.models import Categoria, Endereco, ItemPedido, Pedido, PaymentAttempt, Produto, Restaurante, Usuario
from app.services.payment_providers.contracts import PaymentResult, PaymentStatus
from app.services.payment_service import PaymentService


@pytest.fixture
def app():
    application = Flask("payment_gateway_reconciliation_test")
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="payment-reconciliation-test-secret",
        APP_ENV="testing",
        PAYMENT_PROVIDER="mercadopago",
    )
    db.init_app(application)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.engine.dispose()


def test_consulta_gateway_pendente_preserva_preferencia_sem_confirmar_pedido(app):
    with app.app_context():
        cliente = Usuario(
            nome_completo="Cliente Pagamento",
            email="recon@example.com",
            telefone="+5511998887777",
            cpf="12345678901",
        )
        restaurante = Restaurante(
            cnpj="12345678000191",
            razao_social="Doceria Recon LTDA",
            nome="Doceria Recon",
            cpf_responsavel="98765432100",
            email="recon-restaurante@example.com",
            telefone="+551133332222",
            taxa_entrega_base=0,
            taxa_entrega_por_km=0,
            raio_entrega_km=10,
        )
        db.session.add_all([cliente, restaurante])
        db.session.flush()
        endereco = Endereco(
            id_usuario=cliente.id,
            cep="01001000",
            rua="Rua de Teste",
            numero="10",
            bairro="Centro",
            cidade="São Paulo",
            estado="SP",
            tipo_endereco="RESIDENCIAL",
            principal=True,
            ativo=True,
        )
        categoria = Categoria(id_restaurante=restaurante.id, nome="Doces")
        db.session.add_all([endereco, categoria])
        db.session.flush()
        produto = Produto(
            restaurant_id=restaurante.id,
            category_id=categoria.id,
            name="Brigadeiro",
            description="Teste",
            price=Decimal("10.00"),
            is_available=True,
            is_imported=False,
            current_stock=5,
            allows_customization=False,
        )
        db.session.add(produto)
        db.session.flush()
        pedido = Pedido(
            order_code="CL-RECON-0001",
            user_id=cliente.id,
            restaurant_id=restaurante.id,
            delivery_address_id=endereco.id,
            subtotal=Decimal("10.00"),
            discount=Decimal("0.00"),
            delivery_fee=Decimal("0.00"),
            platform_fee=Decimal("0.00"),
            total=Decimal("10.00"),
            order_type="PICKUP",
            status="PENDENTE_PAGAMENTO",
            payment_method="PIX",
        )
        db.session.add(pedido)
        db.session.flush()
        db.session.add(ItemPedido(
            id_pedido=pedido.id,
            id_produto=produto.id,
            quantidade=1,
            preco_unitario=Decimal("10.00"),
        ))
        tentativa = PaymentAttempt(
            order_id=pedido.id,
            provider="mercadopago",
            provider_payment_id=f"pref:{pedido.id}:preference-123",
            idempotency_key=f"order:{pedido.id}:payment:v1",
            payment_method="PIX",
            status="PENDING",
            amount=Decimal("10.00"),
            currency="BRL",
        )
        db.session.add(tentativa)
        db.session.commit()

        resultado = PaymentService._registrar_resultado_gateway(
            pedido,
            tentativa,
            PaymentResult(
                provider="mercadopago",
                provider_payment_id="payment-123",
                status=PaymentStatus.PENDING,
                amount=Decimal("10.00"),
                currency="BRL",
                message="Pagamento ainda pendente.",
            ),
        )

        atualizada = db.session.get(PaymentAttempt, tentativa.id)
        pedido_atualizado = db.session.get(Pedido, pedido.id)
        assert resultado["success"] is True
        # Mantém a preferência para conseguir reconciliar outra tentativa do Checkout Pro.
        assert atualizada.provider_payment_id == f"pref:{pedido.id}:preference-123"
        assert atualizada.status == "PENDING"
        assert pedido_atualizado.status == "PENDENTE_PAGAMENTO"
