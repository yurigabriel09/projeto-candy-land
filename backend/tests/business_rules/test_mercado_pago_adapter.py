import hashlib
import hmac
import json
from decimal import Decimal

from app.services.payment_providers.contracts import CreatePaymentCommand, PaymentMethod, PaymentStatus
from app.services.payment_providers.mercado_pago_adapter import MercadoPagoPaymentProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.ok = status_code < 400
        self.content = json.dumps(payload).encode("utf-8")

    def json(self):
        return self.payload


def test_create_payment_cria_preferencia_e_usa_url_sandbox(monkeypatch):
    chamadas = []

    def fake_request(method, url, **kwargs):
        chamadas.append((method, url, kwargs))
        return FakeResponse({
            "id": "pref-123",
            "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=pref-123",
            "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout?pref_id=pref-123",
        })

    monkeypatch.setattr("app.services.payment_providers.mercado_pago_adapter.requests.request", fake_request)
    provider = MercadoPagoPaymentProvider({
        "MERCADO_PAGO_ACCESS_TOKEN": "token-falso-para-teste",
        "MERCADO_PAGO_SANDBOX": True,
        "MERCADO_PAGO_RETURN_URL_BASE": "http://localhost:5173",
    })
    command = CreatePaymentCommand(
        order_id="17",
        idempotency_key="pedido-17-v1",
        amount=Decimal("35.50"),
        method=PaymentMethod.PIX,
        metadata={"order_code": "CL-ABC123"},
    )

    result = provider.create_payment(command)

    assert result.provider == "mercadopago"
    assert result.provider_payment_id == "pref:17:pref-123"
    assert result.status is PaymentStatus.PENDING
    assert result.approval_url.startswith("https://sandbox.mercadopago.com.br/")
    assert chamadas[0][1].endswith("/checkout/preferences")
    assert chamadas[0][2]["headers"]["Authorization"] == "Bearer token-falso-para-teste"
    payload = chamadas[0][2]["json"]
    assert payload["external_reference"] == "17"
    assert payload["items"][0]["unit_price"] == 35.5
    assert payload["back_urls"]["success"].startswith("http://localhost:5173/checkout/resultado")
    assert any(item["id"] == "credit_card" for item in payload["payment_methods"]["excluded_payment_types"])
    assert all(item["id"] != "account_money" for item in payload["payment_methods"]["excluded_payment_types"])


def test_webhook_exige_assinatura_e_busca_estado_real(monkeypatch):
    secret = "webhook-secret-falso"
    body = {
        "action": "payment.updated",
        "data": {"id": "998877"},
        "id": "notification-123",
        "type": "payment",
    }
    request_id = "request-123"
    timestamp = "1700000000000"
    manifest = f"id:998877;request-id:{request_id};ts:{timestamp};"
    signature = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    payment = {
        "id": 998877,
        "status": "approved",
        "status_detail": "accredited",
        "transaction_amount": 35.5,
        "currency_id": "BRL",
        "external_reference": "17",
        "payment_type_id": "debit_card",
        "payment_method_id": "visa",
        "date_last_updated": "2026-10-25T12:00:00Z",
    }
    chamadas = []

    def fake_request(method, url, **kwargs):
        chamadas.append((method, url, kwargs))
        return FakeResponse(payment)

    monkeypatch.setattr("app.services.payment_providers.mercado_pago_adapter.requests.request", fake_request)
    provider = MercadoPagoPaymentProvider({
        "MERCADO_PAGO_ACCESS_TOKEN": "token-falso-para-teste",
        "MERCADO_PAGO_WEBHOOK_SECRET": secret,
    })

    event = provider.verify_webhook(
        {"x-signature": f"ts={timestamp},v1={signature}", "x-request-id": request_id},
        json.dumps(body).encode(),
        "998877",  # Mercado Pago signs query data.id, not the event's numeric ID.
    )

    assert event.provider == "mercadopago"
    assert event.provider_payment_id == "998877"
    assert event.order_reference == "17"
    assert event.status is PaymentStatus.APPROVED
    assert event.amount == Decimal("35.50")
    assert event.payment_type_id == "debit_card"
    assert event.payment_method_id == "visa"
    assert chamadas[0][1].endswith("/v1/payments/998877")


def test_webhook_recusa_assinatura_invalida(monkeypatch):
    provider = MercadoPagoPaymentProvider({
        "MERCADO_PAGO_ACCESS_TOKEN": "token-falso-para-teste",
        "MERCADO_PAGO_WEBHOOK_SECRET": "segredo-correto",
    })
    body = json.dumps({"data": {"id": "123"}}).encode()
    try:
        provider.verify_webhook(
            {"x-signature": "ts=1700000000000,v1=assinatura-incorreta", "x-request-id": "req"},
            body,
        )
    except Exception as exc:
        assert "inválida" in str(exc).lower()
    else:
        raise AssertionError("O webhook com assinatura inválida deveria ser recusado.")



def test_create_payment_configura_retorno_automatico_com_url_publica_https(monkeypatch):
    chamadas = []

    def fake_request(method, url, **kwargs):
        chamadas.append((method, url, kwargs))
        return FakeResponse({
            "id": "pref-https-456",
            "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=pref-https-456",
            "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout?pref_id=pref-https-456",
        })

    monkeypatch.setattr("app.services.payment_providers.mercado_pago_adapter.requests.request", fake_request)
    provider = MercadoPagoPaymentProvider({
        "MERCADO_PAGO_ACCESS_TOKEN": "token-falso-para-teste",
        "MERCADO_PAGO_SANDBOX": True,
        "MERCADO_PAGO_RETURN_URL_BASE": "https://candyland.example",
    })
    command = CreatePaymentCommand(
        order_id="31",
        idempotency_key="pedido-31-v1",
        amount=Decimal("12.00"),
        method=PaymentMethod.PIX,
        metadata={"order_code": "CL-RETURN31"},
    )

    provider.create_payment(command)

    payload = chamadas[0][2]["json"]
    assert payload["back_urls"]["success"] == (
        "https://candyland.example/checkout/resultado?order_id=31&return=success"
    )
    assert payload["back_urls"]["pending"].endswith("&return=pending")
    assert payload["back_urls"]["failure"].endswith("&return=failure")
    assert payload["auto_return"] == "approved"


def test_metodo_cartao_generico_preserva_credito_debito_e_exclui_pix_boleto():
    excluded = MercadoPagoPaymentProvider._excluded_types(PaymentMethod.CARD)
    ids = {item["id"] for item in excluded}
    assert "bank_transfer" in ids
    assert "ticket" in ids
    assert "credit_card" not in ids
    assert "debit_card" not in ids
    assert "account_money" not in ids


def test_payment_result_expoe_tipo_real_retorna_do_mercado_pago():
    provider = MercadoPagoPaymentProvider({"MERCADO_PAGO_ACCESS_TOKEN": "token-de-teste"})
    result = provider._payment_result({
        "id": 123,
        "status": "approved",
        "transaction_amount": 12.00,
        "currency_id": "BRL",
        "payment_type_id": "debit_card",
        "payment_method_id": "visa",
    })
    assert result.payment_type_id == "debit_card"
    assert result.payment_method_id == "visa"


def test_webhook_usa_data_id_da_query_quando_body_nao_tem_data_id(monkeypatch):
    secret = "webhook-secret-falso"
    request_id = "request-query-only"
    timestamp = "1700000000123"
    manifest = f"id:abc123;request-id:{request_id};ts:{timestamp};"
    signature = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    payment = {
        "id": "abc123",
        "status": "pending",
        "transaction_amount": 12.0,
        "currency_id": "BRL",
        "external_reference": "17",
        "date_last_updated": "2026-10-25T12:00:00Z",
    }

    def fake_request(method, url, **kwargs):
        return FakeResponse(payment)

    monkeypatch.setattr("app.services.payment_providers.mercado_pago_adapter.requests.request", fake_request)
    provider = MercadoPagoPaymentProvider({
        "MERCADO_PAGO_ACCESS_TOKEN": "token-falso-para-teste",
        "MERCADO_PAGO_WEBHOOK_SECRET": secret,
    })
    event = provider.verify_webhook(
        {"X-Signature": f"TS={timestamp}; V1={signature}", "X-Request-Id": request_id},
        json.dumps({"type": "payment", "action": "payment.updated"}).encode(),
        "abc123",
    )

    assert event.provider_payment_id == "abc123"
    assert event.order_reference == "17"
    assert event.status is PaymentStatus.PENDING
