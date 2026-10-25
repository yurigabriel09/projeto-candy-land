"""Non-production payment adapter for deterministic end-to-end testing.

This provider never contacts a gateway and never moves money. Its simulated
result method is only exposed through routes that are separately restricted to
local/development/test environments.
"""
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, FrozenSet, Mapping, Optional
from uuid import NAMESPACE_URL, uuid5

from app.services.payment_providers.contracts import (
    CreatePaymentCommand,
    PaymentMethod,
    PaymentProvider,
    PaymentProviderError,
    PaymentResult,
    PaymentStatus,
    VerifiedPaymentEvent,
)


class MockPaymentProvider(PaymentProvider):
    def __init__(self):
        self._payments = {}

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "MockPaymentProvider":
        return cls()

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def supported_methods(self) -> FrozenSet[PaymentMethod]:
        return frozenset({PaymentMethod.PIX, PaymentMethod.CREDIT_CARD})

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        self.validar_metodo(command.method)
        deterministic_id = uuid5(
            NAMESPACE_URL, f"candyland-mock:{command.idempotency_key}"
        ).hex
        result = PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"mock_{deterministic_id}",
            status=PaymentStatus.PENDING,
            amount=command.amount,
            currency=command.currency,
            message=(
                "Pagamento fictício pendente. Nenhuma cobrança real foi realizada. "
                "Use o endpoint mock-result somente em ambiente de testes."
            ),
        )
        self._payments[result.provider_payment_id] = result
        return result

    def capture_payment(
        self, provider_payment_id: str, idempotency_key: str
    ) -> PaymentResult:
        result = self._get_in_memory_payment(provider_payment_id)
        return self._store(replace(result, status=PaymentStatus.APPROVED))

    def get_payment(self, provider_payment_id: str) -> PaymentResult:
        return self._get_in_memory_payment(provider_payment_id)

    def cancel_payment(
        self, provider_payment_id: str, idempotency_key: str
    ) -> PaymentResult:
        result = self._get_in_memory_payment(provider_payment_id)
        return self._store(replace(result, status=PaymentStatus.CANCELLED))

    def refund_payment(
        self,
        provider_payment_id: str,
        idempotency_key: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        result = self._get_in_memory_payment(provider_payment_id)
        refund_amount = amount if amount is not None else result.amount
        if Decimal(str(refund_amount)) != result.amount:
            raise PaymentProviderError(
                "O mock suporta apenas reembolso integral nesta versão."
            )
        return self._store(replace(result, status=PaymentStatus.REFUNDED))

    def verify_webhook(
        self, headers: Mapping[str, str], raw_body: bytes
    ) -> VerifiedPaymentEvent:
        raise PaymentProviderError(
            "O provedor mock não recebe webhooks HTTP. Use o endpoint de simulação "
            "autenticado, disponível somente em ambiente não produtivo."
        )

    def simulate_outcome(
        self,
        *,
        provider_payment_id: str,
        order_reference: str,
        amount: Decimal,
        currency: str,
        outcome: str,
    ) -> VerifiedPaymentEvent:
        mapping = {
            "approved": PaymentStatus.APPROVED,
            "rejected": PaymentStatus.REJECTED,
            "pending": PaymentStatus.PENDING,
            "cancelled": PaymentStatus.CANCELLED,
        }
        normalized = str(outcome or "").strip().lower()
        if normalized not in mapping:
            raise ValueError(
                "outcome deve ser approved, rejected, pending ou cancelled."
            )
        event_id = uuid5(
            NAMESPACE_URL, f"candyland-mock-event:{provider_payment_id}:{normalized}"
        ).hex
        return VerifiedPaymentEvent(
            provider=self.provider_name,
            event_id=f"mock_evt_{event_id}",
            provider_payment_id=provider_payment_id,
            order_reference=str(order_reference),
            status=mapping[normalized],
            amount=amount,
            currency=currency,
            occurred_at=datetime.now(timezone.utc),
        )

    def _get_in_memory_payment(self, provider_payment_id: str) -> PaymentResult:
        result = self._payments.get(provider_payment_id)
        if result is None:
            raise PaymentProviderError(
                "Estado efêmero do mock indisponível; consulte a tentativa persistida "
                "por meio de PaymentService."
            )
        return result

    def _store(self, result: PaymentResult) -> PaymentResult:
        self._payments[result.provider_payment_id] = result
        return result
