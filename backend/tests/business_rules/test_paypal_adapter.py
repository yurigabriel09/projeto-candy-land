from decimal import Decimal
from types import SimpleNamespace

import pytest
import requests

from app.services.payment_providers.contracts import (
    CreatePaymentCommand,
    PaymentMethod,
    PaymentProviderError,
    PaymentStatus,
)
from app.services.payment_providers.paypal_adapter import PayPalPaymentProvider


def _config():
    return {
        "PAYPAL_CLIENT_ID": "sandbox-client",
        "PAYPAL_CLIENT_SECRET": "sandbox-secret",
        "PAYPAL_MODE": "sandbox",
        "PAYPAL_WEBHOOK_ID": "WH-test",
        "FRONTEND_URL": "http://localhost:5173",
    }


def _response(payload, status=200):
    return SimpleNamespace(ok=status < 400, status_code=status, content=b"{}", json=lambda: payload)


def _command():
    return CreatePaymentCommand(
        order_id="42",
        idempotency_key="order:42:payment:v1",
        amount=Decimal("35.90"),
        method=PaymentMethod.CARD,
        currency="BRL",
        metadata={"order_code": "CL-42"},
    )


def test_paypal_create_order_uses_server_amount_and_returns_approval_url(monkeypatch):
    api_calls = []
    monkeypatch.setattr(requests, "post", lambda *a, **k: _response({"access_token": "test-access"}))

    def api_request(method, url, **kwargs):
        api_calls.append((method, url, kwargs))
        return _response({
            "id": "PAYPAL-ORDER-42",
            "status": "CREATED",
            "purchase_units": [{"amount": {"currency_code": "BRL", "value": "35.90"}}],
            "links": [{"rel": "approve", "href": "https://www.sandbox.paypal.com/checkoutnow?token=PAYPAL-ORDER-42"}],
        }, 201)

    monkeypatch.setattr(requests, "request", api_request)
    provider = PayPalPaymentProvider.from_config(_config())
    result = provider.create_payment(_command())

    assert result.provider == "paypal"
    assert result.provider_payment_id == "PAYPAL-ORDER-42"
    assert result.amount == Decimal("35.90")
    assert result.currency == "BRL"
    assert result.status is PaymentStatus.PENDING
    assert result.approval_url.startswith("https://")
    payload = api_calls[0][2]["json"]
    assert payload["purchase_units"][0]["amount"]["value"] == "35.90"
    assert payload["purchase_units"][0]["custom_id"] == "42"
    assert api_calls[0][2]["headers"]["PayPal-Request-Id"]


def test_paypal_capture_maps_completed_to_approved_and_keeps_order_id(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: _response({"access_token": "test-access"}))
    monkeypatch.setattr(requests, "request", lambda *a, **k: _response({
        "id": "PAYPAL-ORDER-42",
        "status": "COMPLETED",
        "purchase_units": [{
            "amount": {"currency_code": "BRL", "value": "35.90"},
            "payments": {"captures": [{"id": "CAPTURE-42", "status": "COMPLETED", "amount": {"currency_code": "BRL", "value": "35.90"}}]},
        }],
    }))
    provider = PayPalPaymentProvider.from_config(_config())
    result = provider.capture_payment("PAYPAL-ORDER-42", "capture:42")
    assert result.status is PaymentStatus.APPROVED
    assert result.provider_payment_id == "PAYPAL-ORDER-42"
    assert result.amount == Decimal("35.90")


def test_paypal_rejeita_credenciais_ausentes():
    with pytest.raises(PaymentProviderError, match="PAYPAL_CLIENT_ID"):
        PayPalPaymentProvider.from_config({"PAYPAL_MODE": "sandbox"})


def test_paypal_webhook_only_normalizes_after_api_verification(monkeypatch):
    provider = PayPalPaymentProvider.from_config(_config())
    def fake_request(method, path, payload=None, extra_headers=None):
        if path == "/v1/notifications/verify-webhook-signature":
            return {"verification_status": "SUCCESS"}
        if path == "/v2/checkout/orders/PAYPAL-ORDER-42":
            return {"id": "PAYPAL-ORDER-42", "purchase_units": [{"custom_id": "42", "amount": {"currency_code": "BRL", "value": "35.90"}}]}
        raise AssertionError(f"Chamada inesperada do PayPal: {method} {path}")
    monkeypatch.setattr(provider, "_request", fake_request)
    body = b'{"id":"WH-EVENT-1","event_type":"PAYMENT.CAPTURE.COMPLETED","resource":{"supplementary_data":{"related_ids":{"order_id":"PAYPAL-ORDER-42"}},"amount":{"currency_code":"BRL","value":"35.90"}}}'
    event = provider.verify_webhook({
        "Paypal-Auth-Algo": "SHA256withRSA",
        "Paypal-Cert-Url": "https://api-m.sandbox.paypal.com/cert",
        "Paypal-Transmission-Id": "transmission-1",
        "Paypal-Transmission-Sig": "signature",
        "Paypal-Transmission-Time": "2026-10-27T10:00:00Z",
    }, body)
    assert event.provider == "paypal"
    assert event.order_reference == "42"
    assert event.provider_payment_id == "PAYPAL-ORDER-42"
    assert event.status is PaymentStatus.APPROVED
    assert event.amount == Decimal("35.90")
