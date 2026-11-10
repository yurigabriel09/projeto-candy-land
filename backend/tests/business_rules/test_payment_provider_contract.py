from decimal import Decimal

import pytest

from app.services.payment_providers.contracts import (
    CreatePaymentCommand,
    PaymentMethod,
    PaymentProviderNotSelected,
    PaymentProviderNotImplemented,
    PaymentResult,
    PaymentStatus,
    UnsupportedPaymentMethod,
    VerifiedPaymentEvent,
)
from app.services.payment_providers.factory import get_payment_provider


def test_create_payment_command_normaliza_valor_metodo_e_moeda():
    command = CreatePaymentCommand(
        order_id="42",
        idempotency_key="order:42:create:v1",
        amount="125.5",
        method="PIX",
        currency="brl",
    )

    assert command.amount == Decimal("125.50")
    assert command.method is PaymentMethod.PIX
    assert command.currency == "BRL"


@pytest.mark.parametrize("amount", [0, -1, "NaN", "Infinity", "valor-invalido"])
def test_create_payment_command_rejeita_valor_invalido(amount):
    with pytest.raises(ValueError):
        CreatePaymentCommand(
            order_id="42",
            idempotency_key="order:42:create:v1",
            amount=amount,
            method=PaymentMethod.CREDIT_CARD,
        )


def test_create_payment_command_exige_referencia_e_chave_de_idempotencia():
    with pytest.raises(ValueError, match="order_id"):
        CreatePaymentCommand(
            order_id="",
            idempotency_key="idempotency-42",
            amount=10,
            method=PaymentMethod.PIX,
        )

    with pytest.raises(ValueError, match="idempotency_key"):
        CreatePaymentCommand(
            order_id="42",
            idempotency_key="",
            amount=10,
            method=PaymentMethod.PIX,
        )


def test_payment_result_normaliza_status_sem_exigir_payload_proprietario():
    result = PaymentResult(
        provider="MercadoPago",
        provider_payment_id="provider-123",
        status="PENDING",
        amount="34.90",
        currency="brl",
        pix_copy_paste="copia-e-cola-de-teste",
    )

    assert result.provider == "mercadopago"
    assert result.status is PaymentStatus.PENDING
    assert result.amount == Decimal("34.90")
    assert result.currency == "BRL"
    assert result.pix_copy_paste == "copia-e-cola-de-teste"


def test_evento_de_webhook_tem_contrato_normalizado():
    event = VerifiedPaymentEvent(
        provider="paypal",
        event_id="evt-1",
        provider_payment_id="pay-42",
        order_reference="42",
        status="APPROVED",
        amount="10.00",
    )

    assert event.provider == "paypal"
    assert event.status is PaymentStatus.APPROVED
    assert event.order_reference == "42"


def test_factory_falha_fechada_se_nenhum_provedor_foi_selecionado():
    with pytest.raises(PaymentProviderNotSelected):
        get_payment_provider(config={"PAYMENT_PROVIDER": "none"})


def test_factory_carrega_ambos_os_provedores_reais_sem_chamar_a_rede():
    paypal = get_payment_provider(config={"PAYMENT_PROVIDER": "paypal", "PAYPAL_CLIENT_ID": "id", "PAYPAL_CLIENT_SECRET": "secret", "PAYPAL_MODE": "sandbox"})
    assert paypal.provider_name == "paypal"
    assert paypal.supported_methods == frozenset({PaymentMethod.CARD})

    provider = get_payment_provider(
        config={"PAYMENT_PROVIDER": "mercadopago", "MERCADO_PAGO_ACCESS_TOKEN": "token-de-teste", "MERCADO_PAGO_SANDBOX": True}
    )
    assert provider.provider_name == "mercadopago"
    assert provider.supported_methods == frozenset({PaymentMethod.PIX, PaymentMethod.CARD, PaymentMethod.CREDIT_CARD})


def test_meio_nao_suportado_pelo_provedor_e_rejeitado():
    with pytest.raises(UnsupportedPaymentMethod):
        # Exercise the shared rule without invoking any external gateway.
        from app.services.payment_providers.contracts import PaymentProvider

        class FakeProvider(PaymentProvider):
            @classmethod
            def from_config(cls, config):
                return cls()

            @property
            def provider_name(self):
                return "fake"

            @property
            def supported_methods(self):
                return frozenset({PaymentMethod.PIX})

            def create_payment(self, command):
                raise NotImplementedError

            def capture_payment(self, provider_payment_id, idempotency_key):
                raise NotImplementedError

            def get_payment(self, provider_payment_id):
                raise NotImplementedError

            def cancel_payment(self, provider_payment_id, idempotency_key):
                raise NotImplementedError

            def refund_payment(self, provider_payment_id, idempotency_key, amount=None):
                raise NotImplementedError

            def verify_webhook(self, headers, raw_body):
                raise NotImplementedError

        FakeProvider().validar_metodo(PaymentMethod.BOLETO)
