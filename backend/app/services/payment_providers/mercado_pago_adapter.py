"""Adaptador do Mercado Pago Checkout Pro usando a Preferences API.

O Access Token fica exclusivamente no backend. O checkout redireciona o cliente
para o Mercado Pago e a confirmação é conferida no endpoint oficial de pagamentos
ou por webhook assinado; nunca confiamos apenas na URL de retorno do navegador.
"""
import hashlib
import hmac
import json
from decimal import Decimal
from typing import Any, FrozenSet, Mapping, Optional

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

API_BASE = "https://api.mercadopago.com"


class MercadoPagoPaymentProvider(PaymentProvider):
    def __init__(self, config: Mapping[str, Any]):
        self.access_token = str(config.get("MERCADO_PAGO_ACCESS_TOKEN", "") or "").strip()
        self.webhook_secret = str(config.get("MERCADO_PAGO_WEBHOOK_SECRET", "") or "").strip()
        self.return_url_base = str(
            config.get("MERCADO_PAGO_RETURN_URL_BASE")
            or config.get("FRONTEND_URL")
            or "http://localhost:5173"
        ).strip().rstrip("/")
        self.notification_url = str(config.get("MERCADO_PAGO_NOTIFICATION_URL", "") or "").strip()
        self.sandbox = _as_bool(config.get("MERCADO_PAGO_SANDBOX", True))
        if not self.access_token:
            raise PaymentProviderError(
                "MERCADO_PAGO_ACCESS_TOKEN não configurado no backend/.env."
            )

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "MercadoPagoPaymentProvider":
        return cls(config)

    @property
    def provider_name(self) -> str:
        return "mercadopago"

    @property
    def supported_methods(self) -> FrozenSet[PaymentMethod]:
        return frozenset({PaymentMethod.PIX, PaymentMethod.CARD, PaymentMethod.CREDIT_CARD})

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        self.validar_metodo(command.method)
        return_url = f"{self.return_url_base}/checkout/resultado?order_id={command.order_id}"
        payload: dict[str, Any] = {
            "items": [
                {
                    "id": f"candyland-order-{command.order_id}",
                    "title": f"CandyLand - Pedido {command.metadata.get('order_code', command.order_id)}",
                    "description": "Pedido realizado na plataforma CandyLand",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": float(command.amount),
                }
            ],
            "external_reference": str(command.order_id),
            "metadata": {"order_code": str(command.metadata.get("order_code", ""))},
            "back_urls": {
                "success": f"{return_url}&return=success",
                "pending": f"{return_url}&return=pending",
                "failure": f"{return_url}&return=failure",
            },
            "payment_methods": {"excluded_payment_types": self._excluded_types(command.method)},
        }
        # Mercado Pago só exige o retorno automático em origens HTTPS. Para o
        # teste local em localhost, as URLs de retorno continuam configuradas.
        if self.return_url_base.lower().startswith("https://"):
            payload["auto_return"] = "approved"
        if self.notification_url:
            if not self.notification_url.lower().startswith("https://"):
                raise PaymentProviderError(
                    "MERCADO_PAGO_NOTIFICATION_URL precisa usar HTTPS; deixe vazia no teste local até configurar um túnel HTTPS."
                )
            payload["notification_url"] = self.notification_url

        response = self._request(
            "POST",
            "/checkout/preferences",
            payload,
            extra_headers={"X-Idempotency-Key": command.idempotency_key},
        )
        preference_id = str(response.get("id") or "").strip()
        sandbox_url = str(response.get("sandbox_init_point") or "").strip()
        live_url = str(response.get("init_point") or "").strip()
        approval_url = (sandbox_url or live_url) if self.sandbox else (live_url or sandbox_url)
        if not preference_id or not approval_url:
            raise PaymentProviderError(
                "O Mercado Pago não retornou o ID da preferência e a URL de checkout esperados."
            )
        # Guardamos o ID da ordem junto do ID da preferência para pesquisar o
        # pagamento real antes da notificação ou quando o comprador retorna.
        preference_reference = f"pref:{command.order_id}:{preference_id}"
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=preference_reference,
            status=PaymentStatus.PENDING,
            amount=command.amount,
            currency="BRL",
            approval_url=approval_url,
            message="Preferência de checkout criada. Aguardando confirmação do Mercado Pago.",
        )

    def get_payment(self, provider_payment_id: str) -> PaymentResult:
        raw_id = str(provider_payment_id or "").strip()
        if raw_id.startswith("pref:"):
            parts = raw_id.split(":", 2)
            if len(parts) != 3 or not parts[1] or not parts[2]:
                raise PaymentProviderError("Referência da preferência do Mercado Pago inválida.")
            order_id = parts[1]
            search = self._request(
                "GET",
                "/v1/payments/search",
                params={
                    "external_reference": order_id,
                    "sort": "date_created",
                    "criteria": "desc",
                    "limit": 1,
                },
            )
            results = search.get("results") or []
            if not results:
                raise PaymentProviderError("O Mercado Pago ainda não registrou um pagamento para este pedido.")
            return self._payment_result(results[0])
        if not raw_id:
            raise PaymentProviderError("ID do pagamento do Mercado Pago ausente.")
        payment = self._request("GET", f"/v1/payments/{raw_id}")
        return self._payment_result(payment)

    def capture_payment(self, provider_payment_id: str, idempotency_key: str) -> PaymentResult:
        # Checkout Pro gerencia a experiência e a aprovação no site do gateway;
        # não há captura manual deste objeto de preferência neste adaptador.
        return self.get_payment(provider_payment_id)

    def cancel_payment(self, provider_payment_id: str, idempotency_key: str) -> PaymentResult:
        if str(provider_payment_id).startswith("pref:"):
            raise PaymentProviderError(
                "Não é possível cancelar uma preferência antes que o Mercado Pago crie um pagamento."
            )
        result = self._request(
            "PUT",
            f"/v1/payments/{provider_payment_id}",
            {"status": "cancelled"},
            extra_headers={"X-Idempotency-Key": idempotency_key},
        )
        return self._payment_result(result)

    def refund_payment(
        self,
        provider_payment_id: str,
        idempotency_key: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        if str(provider_payment_id).startswith("pref:"):
            raise PaymentProviderError(
                "O pedido ainda não tem um ID de pagamento confirmado para reembolso."
            )
        payload = {"amount": float(amount)} if amount is not None else {}
        self._request(
            "POST",
            f"/v1/payments/{provider_payment_id}/refunds",
            payload,
            extra_headers={"X-Idempotency-Key": idempotency_key},
        )
        return self.get_payment(str(provider_payment_id))

    def verify_webhook(
        self,
        headers: Mapping[str, str],
        raw_body: bytes,
        query_data_id: Optional[str] = None,
    ) -> VerifiedPaymentEvent:
        if not self.webhook_secret:
            raise PaymentProviderError(
                "MERCADO_PAGO_WEBHOOK_SECRET não configurado; configure o segredo em Integrações > Webhooks."
            )
        try:
            body = json.loads(raw_body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PaymentProviderError("Corpo do webhook do Mercado Pago inválido.") from exc
        body_data_id = str(((body.get("data") or {}).get("id")) or "").strip()
        # Mercado Pago signs the data.id query parameter. Some callbacks also
        # include the same value in JSON body.data.id; the URL value is source
        # of truth for HMAC verification and must be passed by the route.
        data_id = str(query_data_id or body_data_id).strip()
        if query_data_id and body_data_id and query_data_id.strip().lower() != body_data_id.strip().lower():
            raise PaymentProviderError(
                "O data.id da URL não corresponde ao identificador do corpo do webhook."
            )
        signature = _header(headers, "x-signature")
        request_id = _header(headers, "x-request-id")
        parsed = _parse_signature(signature)
        timestamp = parsed.get("ts")
        received_signature = parsed.get("v1")
        if not data_id or not timestamp or not received_signature:
            raise PaymentProviderError("Assinatura ou identificador do webhook ausente.")

        manifest = f"id:{data_id.lower()};"
        if request_id:
            manifest += f"request-id:{request_id};"
        manifest += f"ts:{timestamp};"
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, received_signature):
            raise PaymentProviderError("Assinatura do webhook do Mercado Pago inválida.")

        payment = self._request("GET", f"/v1/payments/{data_id}")
        result = self._payment_result(payment)
        order_reference = str(payment.get("external_reference") or "").strip()
        if not order_reference:
            raise PaymentProviderError("O pagamento recebido não contém referência externa do pedido.")
        event_id = str(
            body.get("id")
            or f"mp:{data_id}:{payment.get('status')}:{payment.get('date_last_updated') or timestamp}"
        )
        return VerifiedPaymentEvent(
            provider=self.provider_name,
            event_id=event_id,
            provider_payment_id=result.provider_payment_id,
            order_reference=order_reference,
            status=result.status,
            amount=result.amount,
            currency=result.currency,
            occurred_at=None,
            payment_type_id=str(payment.get("payment_type_id") or "").strip() or None,
            payment_method_id=str(payment.get("payment_method_id") or "").strip() or None,
        )

    def _payment_result(self, data: Mapping[str, Any]) -> PaymentResult:
        status_map = {
            "approved": PaymentStatus.APPROVED,
            "pending": PaymentStatus.PENDING,
            "in_process": PaymentStatus.PENDING,
            "authorized": PaymentStatus.PENDING,
            "rejected": PaymentStatus.REJECTED,
            "cancelled": PaymentStatus.CANCELLED,
            "refunded": PaymentStatus.REFUNDED,
            "charged_back": PaymentStatus.REFUNDED,
        }
        status = status_map.get(str(data.get("status") or "").lower(), PaymentStatus.UNKNOWN)
        amount = data.get("transaction_amount") or data.get("transaction_amount_refunded")
        if amount is None:
            raise PaymentProviderError("A resposta do Mercado Pago não contém o valor do pagamento.")
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=str(data.get("id") or "").strip(),
            status=status,
            amount=Decimal(str(amount)).quantize(Decimal("0.01")),
            currency=str(data.get("currency_id") or "BRL"),
            message=str(data.get("status_detail") or data.get("status") or "Estado consultado no Mercado Pago."),
            payment_type_id=str(data.get("payment_type_id") or "").strip() or None,
            payment_method_id=str(data.get("payment_method_id") or "").strip() or None,
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        headers.update(extra_headers or {})
        try:
            response = requests.request(
                method,
                f"{API_BASE}{path}",
                headers=headers,
                json=payload,
                params=params,
                timeout=20,
            )
        except requests.RequestException as exc:
            raise PaymentProviderError(
                "Não foi possível conectar ao Mercado Pago. Verifique a conexão e tente novamente."
            ) from exc
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {}
        if not response.ok:
            # Nunca inclua token/headers na mensagem de erro retornada ao cliente.
            message = data.get("message") or data.get("error") or "solicitação recusada"
            causes = data.get("cause") or []
            detail = causes[0].get("description") if causes and isinstance(causes[0], dict) else None
            raise PaymentProviderError(
                f"Mercado Pago respondeu HTTP {response.status_code}: {detail or message}."
            )
        if not isinstance(data, dict):
            raise PaymentProviderError("Resposta inesperada do Mercado Pago.")
        return data

    @staticmethod
    def _excluded_types(method: PaymentMethod) -> list[dict[str, str]]:
        # Não exclua account_money: o Mercado Pago rejeita essa exclusão (HTTP 400).
        # O usuário escolhe PIX ou Cartão no CandyLand; para Cartão, retiramos PIX
        # e boleto do checkout, permitindo que o gateway identifique crédito/débito.
        if method is PaymentMethod.PIX:
            excluded = ("credit_card", "debit_card", "prepaid_card", "ticket", "atm")
        else:
            excluded = ("bank_transfer", "ticket", "atm")
        return [{"id": item} for item in excluded]


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _header(headers: Mapping[str, str], name: str) -> str:
    target = name.lower()
    return str(next((v for k, v in headers.items() if str(k).lower() == target), "") or "").strip()


def _parse_signature(signature: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    # The documented header is comma-separated; also tolerate semicolons and
    # casing/whitespace variations introduced by intermediaries or test tools.
    for part in str(signature or "").replace(";", ",").split(","):
        if "=" in part:
            key, value = part.strip().split("=", 1)
            parsed[key.strip().lower()] = value.strip().strip('"')
    return parsed
