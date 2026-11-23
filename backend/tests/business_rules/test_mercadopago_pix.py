from decimal import Decimal

from app.services.payment_providers.contracts import (
    CreatePaymentCommand,
    PaymentMethod,
    PaymentStatus,
)
from app.services.payment_providers.mercado_pago_adapter import (
    MercadoPagoPaymentProvider,
)


def test_mercadopago_pix_cria_order_e_retorna_qr_code_sem_redirect():
    provider = MercadoPagoPaymentProvider({"MERCADO_PAGO_ACCESS_TOKEN": "test-token", "MERCADO_PAGO_SANDBOX": True})
    calls = []

    def fake_request(method, path, payload=None, params=None, extra_headers=None):
        calls.append((method, path, payload, extra_headers))
        return {
        "id": "ORD-PIX-42",
        "external_reference": "42",
        "status": "action_required",
        "status_detail": "waiting_transfer",
        "total_amount": "35.90",
        "transactions": {"payments": [{
            "amount": "35.90",
            "status": "action_required",
            "status_detail": "waiting_transfer",
            "payment_method": {
                "id": "pix",
                "type": "bank_transfer",
                "qr_code": "000201-pix-copia-cola",
                "qr_code_base64": "aGVsbG8=",
                "ticket_url": "https://www.mercadopago.com.br/ticket/42"
            }
        }]}
    }

    provider._request = fake_request
    command = CreatePaymentCommand(
        order_id="42", idempotency_key="order:42:pix:v1", amount=Decimal("35.90"),
        method=PaymentMethod.PIX, payer_email="cliente@example.com", metadata={"order_code": "CL-42"},
    )
    result = provider.create_payment(command)

    assert calls[0][0:2] == ("POST", "/v1/orders")
    assert calls[0][2]["type"] == "online"
    assert calls[0][2]["external_reference"] == "42"
    assert calls[0][2]["total_amount"] == "35.90"
    assert calls[0][3]["X-Idempotency-Key"] == "order:42:pix:v1"
    assert result.provider_payment_id == "ord:ORD-PIX-42"
    assert result.status is PaymentStatus.PENDING
    assert result.pix_copy_paste == "000201-pix-copia-cola"
    assert result.pix_qr_code_base64 == "aGVsbG8="
    assert result.approval_url == "https://www.mercadopago.com.br/ticket/42"
