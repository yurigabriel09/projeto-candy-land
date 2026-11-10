from decimal import Decimal

from app.services.payment_providers.contracts import CreatePaymentCommand, PaymentMethod, PaymentStatus
from app.services.payment_providers.mercado_pago_adapter import MercadoPagoPaymentProvider


def test_mercadopago_pix_retorna_qr_code_e_copia_e_cola_sem_redirect():
    provider = MercadoPagoPaymentProvider({"MERCADO_PAGO_ACCESS_TOKEN": "test-token", "MERCADO_PAGO_SANDBOX": True})
    calls = []
    def fake_request(method, path, payload=None, params=None, extra_headers=None):
        calls.append((method, path, payload, extra_headers))
        return {
            "id": 12345,
            "status": "pending",
            "status_detail": "pending_waiting_transfer",
            "transaction_amount": 35.90,
            "currency_id": "BRL",
            "payment_method_id": "pix",
            "payment_type_id": "bank_transfer",
            "point_of_interaction": {"transaction_data": {
                "qr_code": "000201-pix-copia-cola",
                "qr_code_base64": "aGVsbG8=",
                "ticket_url": "https://www.mercadopago.com.br/ticket/12345",
            }},
        }
    provider._request = fake_request
    command = CreatePaymentCommand(
        order_id="42", idempotency_key="order:42:pix:v1", amount=Decimal("35.90"),
        method=PaymentMethod.PIX, payer_email="cliente@example.com", metadata={"order_code": "CL-42"},
    )
    result = provider.create_payment(command)
    assert calls[0][0:2] == ("POST", "/v1/payments")
    assert calls[0][2]["payment_method_id"] == "pix"
    assert calls[0][2]["external_reference"] == "42"
    assert calls[0][3]["X-Idempotency-Key"] == "order:42:pix:v1"
    assert result.provider_payment_id == "12345"
    assert result.status is PaymentStatus.PENDING
    assert result.pix_copy_paste == "000201-pix-copia-cola"
    assert result.pix_qr_code_base64 == "aGVsbG8="
    assert result.approval_url == "https://www.mercadopago.com.br/ticket/12345"
