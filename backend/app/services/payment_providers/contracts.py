"""Normalized payment domain contract shared by gateway adapters.

This module contains no network calls, secrets, persistence, or gateway-specific
payloads. Each provider adapter must translate its API to/from these types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, FrozenSet, Mapping, Optional


class PaymentProviderError(RuntimeError):
    """Base exception for expected payment-provider failures."""


class PaymentProviderNotSelected(PaymentProviderError):
    """No active provider was selected in configuration."""


class UnsupportedPaymentProvider(PaymentProviderError):
    """A provider name outside the supported adapter contract was requested."""


class PaymentProviderNotImplemented(PaymentProviderError):
    """The provider is known to the architecture but its adapter is not present."""


class UnsupportedPaymentMethod(PaymentProviderError):
    """The selected provider does not support the requested payment method."""


class PaymentMethod(str, Enum):
    """Canonical CandyLand payment methods; these are not provider names."""

    PIX = "PIX"
    CREDIT_CARD = "CARTAO_CREDITO"
    DEBIT_CARD = "CARTAO_DEBITO"
    BOLETO = "BOLETO"


class PaymentStatus(str, Enum):
    """Provider-independent payment lifecycle states."""

    CREATED = "CREATED"
    PENDING = "PENDING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    UNKNOWN = "UNKNOWN"


def _normalizar_valor(valor: Any) -> Decimal:
    try:
        valor_decimal = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("O valor do pagamento deve ser um decimal válido.") from exc

    if not valor_decimal.is_finite() or valor_decimal <= 0:
        raise ValueError("O valor do pagamento deve ser maior que zero e finito.")

    return valor_decimal.quantize(Decimal("0.01"))


def _normalizar_moeda(moeda: str) -> str:
    moeda_normalizada = str(moeda or "").strip().upper()
    if len(moeda_normalizada) != 3 or not moeda_normalizada.isalpha():
        raise ValueError("A moeda deve ser um código ISO 4217 de três letras.")
    return moeda_normalizada


@dataclass(frozen=True)
class CreatePaymentCommand:
    """Internal instruction to create a payment for an already persisted order.

    `amount` must be obtained from the backend's persisted order total, never
    from a frontend-provided total. `idempotency_key` must remain stable across
    retries of the same logical operation.
    """

    order_id: str
    idempotency_key: str
    amount: Decimal
    method: PaymentMethod
    currency: str = "BRL"
    return_url: Optional[str] = None
    payer_email: Optional[str] = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.order_id or "").strip():
            raise ValueError("order_id é obrigatório.")
        if not str(self.idempotency_key or "").strip():
            raise ValueError("idempotency_key é obrigatório.")
        object.__setattr__(self, "amount", _normalizar_valor(self.amount))
        object.__setattr__(self, "currency", _normalizar_moeda(self.currency))
        try:
            object.__setattr__(self, "method", PaymentMethod(self.method))
        except ValueError as exc:
            raise ValueError("Método de pagamento não suportado pelo contrato.") from exc
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


@dataclass(frozen=True)
class PaymentResult:
    """Normalized result returned from create/capture/query/cancel/refund calls.

    Fields specific to a payment rail are optional. For example, a Pix response
    may contain `pix_copy_paste`; a boleto response may contain `boleto_url`.
    Do not store complete provider responses here: they may contain PII/secrets.
    """

    provider: str
    provider_payment_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str = "BRL"
    approval_url: Optional[str] = None
    pix_copy_paste: Optional[str] = None
    pix_qr_code_base64: Optional[str] = None
    boleto_url: Optional[str] = None
    boleto_line: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None

    def __post_init__(self) -> None:
        if not str(self.provider or "").strip():
            raise ValueError("provider é obrigatório no resultado normalizado.")
        if not str(self.provider_payment_id or "").strip():
            raise ValueError("provider_payment_id é obrigatório.")
        object.__setattr__(self, "provider", self.provider.strip().lower())
        object.__setattr__(self, "status", PaymentStatus(self.status))
        object.__setattr__(self, "amount", _normalizar_valor(self.amount))
        object.__setattr__(self, "currency", _normalizar_moeda(self.currency))


@dataclass(frozen=True)
class VerifiedPaymentEvent:
    """Normalized webhook event returned only after provider verification.

    An adapter's `verify_webhook` MUST authenticate the original request using
    the provider's documented signature/verification mechanism before returning
    this object. Callers must deduplicate by (provider, event_id) and correlate
    the external reference with an existing CandyLand order.
    """

    provider: str
    event_id: str
    provider_payment_id: str
    order_reference: str
    status: PaymentStatus
    amount: Decimal
    currency: str = "BRL"
    occurred_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        required = {
            "provider": self.provider,
            "event_id": self.event_id,
            "provider_payment_id": self.provider_payment_id,
            "order_reference": self.order_reference,
        }
        for field_name, value in required.items():
            if not str(value or "").strip():
                raise ValueError(f"{field_name} é obrigatório no evento verificado.")
        object.__setattr__(self, "provider", self.provider.strip().lower())
        object.__setattr__(self, "status", PaymentStatus(self.status))
        object.__setattr__(self, "amount", _normalizar_valor(self.amount))
        object.__setattr__(self, "currency", _normalizar_moeda(self.currency))


class PaymentProvider(ABC):
    """Adapter interface: one implementation per payment gateway/provider."""

    @classmethod
    @abstractmethod
    def from_config(cls, config: Mapping[str, Any]) -> "PaymentProvider":
        """Build the adapter using server-side config/secrets only."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Stable provider identifier, e.g. `paypal` or `mercadopago`."""

    @property
    @abstractmethod
    def supported_methods(self) -> FrozenSet[PaymentMethod]:
        """Payment rails enabled for this specific account/adapter configuration."""

    def validar_metodo(self, method: PaymentMethod) -> None:
        try:
            normalized = PaymentMethod(method)
        except ValueError as exc:
            raise UnsupportedPaymentMethod("Método de pagamento desconhecido.") from exc
        if normalized not in self.supported_methods:
            raise UnsupportedPaymentMethod(
                f"O provedor {self.provider_name} não oferece {normalized.value} "
                "na configuração atual."
            )

    @abstractmethod
    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        """Create a provider payment/session with a stable idempotency key."""

    @abstractmethod
    def capture_payment(
        self, provider_payment_id: str, idempotency_key: str
    ) -> PaymentResult:
        """Capture/complete a payment when the chosen provider requires it."""

    @abstractmethod
    def get_payment(self, provider_payment_id: str) -> PaymentResult:
        """Retrieve the provider's authoritative payment state."""

    @abstractmethod
    def cancel_payment(
        self, provider_payment_id: str, idempotency_key: str
    ) -> PaymentResult:
        """Cancel an unpaid/authorised payment when supported."""

    @abstractmethod
    def refund_payment(
        self,
        provider_payment_id: str,
        idempotency_key: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        """Refund all or part of a captured payment when supported."""

    @abstractmethod
    def verify_webhook(
        self, headers: Mapping[str, str], raw_body: bytes
    ) -> VerifiedPaymentEvent:
        """Authenticate then normalize a provider webhook; reject invalid signatures."""
