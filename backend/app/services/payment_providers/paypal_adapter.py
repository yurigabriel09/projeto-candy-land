"""PayPal Orders v2 adapter. All credentials and API calls stay on the backend."""
import hashlib
from decimal import Decimal
from typing import Any, FrozenSet, Mapping, Optional
from urllib.parse import urlencode

import requests

from app.services.payment_providers.contracts import (
    CreatePaymentCommand,
    PaymentMethod,
    PaymentProvider,
    PaymentProviderError,
    PaymentResult,
    PaymentStatus,
    VerifiedPaymentEvent,
)


class PayPalPaymentProvider(PaymentProvider):
    def __init__(self, config: Mapping[str, Any]):
        self.client_id = str(config.get("PAYPAL_CLIENT_ID", "") or "").strip()
        self.client_secret = str(config.get("PAYPAL_CLIENT_SECRET", "") or "").strip()
        mode = str(config.get("PAYPAL_MODE", "sandbox") or "sandbox").strip().lower()
        configured_base = str(config.get("PAYPAL_API_BASE", "") or "").strip().rstrip("/")
        live_modes = {"live", "production", "prod"}
        self.api_base = configured_base or (
            "https://api-m.paypal.com"
            if mode in live_modes
            else "https://api-m.sandbox.paypal.com"
        )
        self.webhook_id = str(config.get("PAYPAL_WEBHOOK_ID", "") or "").strip()
        self.return_url_base = str(
            config.get("PAYPAL_RETURN_URL_BASE") or config.get("FRONTEND_URL") or "http://localhost:5173"
        ).strip().rstrip("/")
        if not self.client_id or not self.client_secret:
            raise PaymentProviderError(
                "PAYPAL_CLIENT_ID e PAYPAL_CLIENT_SECRET precisam ser configurados no backend/.env."
            )
        if not self.api_base.startswith("https://"):
            raise PaymentProviderError("PAYPAL_API_BASE precisa usar HTTPS.")
        if mode not in {"sandbox", "live", "production", "prod"}:
            raise PaymentProviderError("PAYPAL_MODE deve ser sandbox ou live.")

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "PayPalPaymentProvider":
        return cls(config)

    @property
    def provider_name(self) -> str:
        return "paypal"

    @property
    def supported_methods(self) -> FrozenSet[PaymentMethod]:
        return frozenset({PaymentMethod.CARD})

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        self.validar_metodo(command.method)
        query = urlencode({"order_id": command.order_id, "provider": "paypal"})
        return_url = f"{self.return_url_base}/checkout/resultado?{query}"
        cancel_query = urlencode({"order_id": command.order_id, "provider": "paypal", "cancel": "1"})
        cancel_url = f"{self.return_url_base}/checkout/resultado?{cancel_query}"
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": str(command.order_id),
                    "custom_id": str(command.order_id),
                    "description": f"CandyLand - Pedido {command.metadata.get('order_code', command.order_id)}",
                    "amount": {
                        "currency_code": command.currency,
                        "value": f"{command.amount:.2f}",
                    },
                }
            ],
            "application_context": {
                "brand_name": "CandyLand",
                "user_action": "PAY_NOW",
                "return_url": return_url,
                "cancel_url": cancel_url,
            },
        }
        request_id = _idempotency_id(command.idempotency_key)
        response = self._request(
            "POST", "/v2/checkout/orders", payload,
            extra_headers={"PayPal-Request-Id": request_id},
        )
        order_id = str(response.get("id") or "").strip()
        approve_url = next(
            (str(link.get("href")) for link in response.get("links", [])
             if str(link.get("rel", "")).lower() in {"approve", "payer-action"} and link.get("href")),
            None,
        )
        amount, currency = _order_amount(response)
        if not order_id or not approve_url:
            raise PaymentProviderError("O PayPal não retornou o ID e a URL de aprovação esperados.")
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=order_id,
            status=PaymentStatus.PENDING,
            amount=amount,
            currency=currency,
            approval_url=approve_url,
            message="Ordem PayPal criada. Aguardando aprovação e captura no servidor.",
        )

    def capture_payment(self, provider_payment_id: str, idempotency_key: str) -> PaymentResult:
        order_id = str(provider_payment_id or "").strip()
        if not order_id:
            raise PaymentProviderError("ID da ordem PayPal ausente.")
        try:
            response = self._request(
                "POST", f"/v2/checkout/orders/{order_id}/capture", {},
                extra_headers={"PayPal-Request-Id": _idempotency_id(idempotency_key)},
            )
        except PaymentProviderError as exc:
            # A browser may retry after the capture succeeded but the response was
            # lost. Re-query the order before returning an error; never capture a
            # different order ID supplied by the client.
            try:
                current = self.get_payment(order_id)
                if current.status is PaymentStatus.APPROVED:
                    return current
            except PaymentProviderError:
                pass
            raise exc
        return self._payment_result(response, expected_order_id=order_id)

    def get_payment(self, provider_payment_id: str) -> PaymentResult:
        order_id = str(provider_payment_id or "").strip()
        if not order_id:
            raise PaymentProviderError("ID da ordem PayPal ausente.")
        response = self._request("GET", f"/v2/checkout/orders/{order_id}")
        return self._payment_result(response, expected_order_id=order_id)

    def cancel_payment(self, provider_payment_id: str, idempotency_key: str) -> PaymentResult:
        current = self.get_payment(provider_payment_id)
        if current.status is PaymentStatus.APPROVED:
            raise PaymentProviderError("A ordem PayPal já foi capturada; é necessário solicitar reembolso.")
        # Orders v2 does not expose a general order-cancel endpoint for this flow.
        raise PaymentProviderError("O PayPal não oferece cancelamento direto desta ordem; deixe a ordem expirar ou cancele no painel.")

    def refund_payment(
        self, provider_payment_id: str, idempotency_key: str, amount: Optional[Decimal] = None
    ) -> PaymentResult:
        order_id = str(provider_payment_id or "").strip()
        order = self._request("GET", f"/v2/checkout/orders/{order_id}")
        units = order.get("purchase_units") or []
        captures = ((units[0].get("payments") or {}).get("captures") or []) if units else []
        capture = next((item for item in captures if item.get("id") and item.get("status") == "COMPLETED"), None)
        if not capture:
            raise PaymentProviderError("Não foi encontrada uma captura concluída para reembolsar no PayPal.")
        payload = {"amount": {"currency_code": "BRL", "value": f"{Decimal(str(amount)):.2f}"}} if amount is not None else {}
        result = self._request(
            "POST", f"/v2/payments/captures/{capture['id']}/refund", payload,
            extra_headers={"PayPal-Request-Id": _idempotency_id(idempotency_key)},
        )
        refund_status = str(result.get("status") or "").upper()
        if refund_status not in {"COMPLETED", "PENDING"}:
            raise PaymentProviderError("O PayPal não confirmou o reembolso; consulte a transação no painel.")
        original_amount, currency = _order_amount(order)
        return PaymentResult(
            provider="paypal", provider_payment_id=order_id,
            status=PaymentStatus.REFUNDED if refund_status == "COMPLETED" else PaymentStatus.PENDING,
            amount=Decimal(str(amount)).quantize(Decimal("0.01")) if amount is not None else original_amount,
            currency=currency, message=f"Reembolso PayPal: {refund_status.lower()}.",
        )

    def verify_webhook(
        self, headers: Mapping[str, str], raw_body: bytes, query_data_id: Optional[str] = None
    ) -> VerifiedPaymentEvent:
        if not self.webhook_id:
            raise PaymentProviderError("PAYPAL_WEBHOOK_ID não configurado; cadastre o webhook no painel PayPal.")
        import json
        try:
            body = json.loads(raw_body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, ValueError) as exc:
            raise PaymentProviderError("Corpo do webhook PayPal inválido.") from exc
        def header(name):
            wanted = name.lower()
            return str(next((v for k, v in headers.items() if str(k).lower() == wanted), "") or "").strip()
        verification = {
            "auth_algo": header("paypal-auth-algo"),
            "cert_url": header("paypal-cert-url"),
            "transmission_id": header("paypal-transmission-id"),
            "transmission_sig": header("paypal-transmission-sig"),
            "transmission_time": header("paypal-transmission-time"),
            "webhook_id": self.webhook_id,
            "webhook_event": body,
        }
        if not all(verification[key] for key in ("auth_algo", "cert_url", "transmission_id", "transmission_sig", "transmission_time")):
            raise PaymentProviderError("Headers de assinatura do webhook PayPal ausentes.")
        check = self._request("POST", "/v1/notifications/verify-webhook-signature", verification)
        if str(check.get("verification_status") or "").upper() != "SUCCESS":
            raise PaymentProviderError("Assinatura do webhook PayPal inválida.")

        event_type = str(body.get("event_type") or "").upper()
        resource = body.get("resource") or {}
        related = ((resource.get("supplementary_data") or {}).get("related_ids") or {})
        paypal_order_id = str(related.get("order_id") or "").strip()
        if not paypal_order_id:
            raise PaymentProviderError("O webhook PayPal não contém o ID externo da ordem para conciliação.")

        # Capture webhook resources don't consistently include purchase-unit
        # custom_id. After verifying the webhook, retrieve the PayPal Order and
        # correlate its persisted CandyLand custom_id and authoritative amount.
        order_data = self._request("GET", f"/v2/checkout/orders/{paypal_order_id}")
        units = order_data.get("purchase_units") or []
        unit = units[0] if units else {}
        order_reference = str(
            unit.get("custom_id") or unit.get("reference_id")
            or resource.get("custom_id") or resource.get("invoice_id") or ""
        ).strip()
        if not order_reference:
            raise PaymentProviderError("A ordem PayPal não contém a referência CandyLand.")

        status_map = {
            "PAYMENT.CAPTURE.COMPLETED": PaymentStatus.APPROVED,
            "PAYMENT.CAPTURE.PENDING": PaymentStatus.PENDING,
            "PAYMENT.CAPTURE.DENIED": PaymentStatus.REJECTED,
            "PAYMENT.CAPTURE.REFUNDED": PaymentStatus.REFUNDED,
            "PAYMENT.CAPTURE.REVERSED": PaymentStatus.REFUNDED,
        }
        status = status_map.get(event_type, PaymentStatus.UNKNOWN)
        amount_info = resource.get("amount") or unit.get("amount") or {}
        if not amount_info:
            raise PaymentProviderError("O webhook PayPal não contém o valor da captura.")
        amount = Decimal(str(amount_info.get("value") or "0")).quantize(Decimal("0.01"))
        currency = str(amount_info.get("currency_code") or unit.get("amount", {}).get("currency_code") or "BRL")
        return VerifiedPaymentEvent(
            provider="paypal",
            event_id=str(body.get("id") or f"paypal:{event_type}:{resource.get('id', order_id)}"),
            provider_payment_id=paypal_order_id,
            order_reference=order_reference,
            status=status,
            amount=amount,
            currency=currency,
        )

    def _request(
        self, method: str, path: str, payload: Optional[dict[str, Any]] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        try:
            token_response = requests.post(
                f"{self.api_base}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json", "Accept-Language": "en_US"},
                timeout=15,
            )
        except requests.RequestException as exc:
            raise PaymentProviderError("Não foi possível conectar à autenticação do PayPal.") from exc
        if not token_response.ok:
            raise PaymentProviderError(f"PayPal OAuth respondeu HTTP {token_response.status_code}.")
        try:
            access_token = str(token_response.json().get("access_token") or "").strip()
        except (ValueError, AttributeError) as exc:
            raise PaymentProviderError("Resposta OAuth inválida do PayPal.") from exc
        if not access_token:
            raise PaymentProviderError("O PayPal não retornou um access token.")

        request_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Prefer": "return=representation"}
        request_headers.update(extra_headers or {})
        try:
            response = requests.request(
                method, f"{self.api_base}{path}", headers=request_headers,
                json=payload, timeout=20,
            )
        except requests.RequestException as exc:
            raise PaymentProviderError("Não foi possível conectar à API do PayPal.") from exc
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {}
        if not response.ok:
            details = data.get("details") or []
            detail = details[0].get("description") if details and isinstance(details[0], dict) else None
            message = detail or data.get("message") or data.get("name") or "requisição recusada"
            raise PaymentProviderError(f"PayPal respondeu HTTP {response.status_code}: {message}.")
        if not isinstance(data, dict):
            raise PaymentProviderError("Resposta inesperada da API PayPal.")
        return data

    @staticmethod
    def _payment_result(data: Mapping[str, Any], expected_order_id: str) -> PaymentResult:
        units = data.get("purchase_units") or []
        unit = units[0] if units else {}
        captures = ((unit.get("payments") or {}).get("captures") or [])
        capture = next((item for item in captures if item.get("status") == "COMPLETED"), None)
        amount_data = (capture or {}).get("amount") or unit.get("amount") or {}
        try:
            amount = Decimal(str(amount_data.get("value"))).quantize(Decimal("0.01"))
        except Exception as exc:
            raise PaymentProviderError("A resposta PayPal não contém o valor do pedido.") from exc
        currency = str(amount_data.get("currency_code") or "BRL")
        status_raw = str(data.get("status") or "").upper()
        if status_raw == "COMPLETED" or capture:
            status = PaymentStatus.APPROVED
        elif status_raw == "PAYER_ACTION_REQUIRED":
            status = PaymentStatus.ACTION_REQUIRED
        else:
            # PayPal order APPROVED only means the buyer approved; funds must
            # still be captured by the trusted backend endpoint.
            status = PaymentStatus.PENDING
        return PaymentResult(
            provider="paypal", provider_payment_id=expected_order_id,
            status=status, amount=amount, currency=currency,
            message=f"PayPal: {status_raw.lower() or 'status desconhecido'}.",
        )


def _order_amount(data: Mapping[str, Any]):
    units = data.get("purchase_units") or []
    if not units:
        raise PaymentProviderError("A ordem PayPal não contém unidade de compra.")
    amount = units[0].get("amount") or {}
    try:
        value = Decimal(str(amount.get("value"))).quantize(Decimal("0.01"))
    except Exception as exc:
        raise PaymentProviderError("A ordem PayPal não contém um valor válido.") from exc
    return value, str(amount.get("currency_code") or "BRL")


def _idempotency_id(value: str) -> str:
    # PayPal-Request-Id is kept stable across retries, within the provider's
    # documented length limits, without transmitting arbitrary client text.
    return hashlib.sha256(str(value or "candyland-payment").encode("utf-8")).hexdigest()[:32]
