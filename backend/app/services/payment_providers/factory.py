"""Select a payment-provider adapter without coupling order logic to a gateway.

The concrete adapters are intentionally not part of this patch because provider
implementation has a separate owner/task. Until one exists, this factory fails
closed instead of falling back to a fake payment or changing order status.
"""

import importlib
import os
from typing import Any, Mapping, Optional

from app.services.payment_providers.contracts import (
    PaymentProvider,
    PaymentProviderNotImplemented,
    PaymentProviderNotSelected,
    UnsupportedPaymentProvider,
)


PAYMENT_PROVIDER_ADAPTERS = {
    "paypal": (
        "app.services.payment_providers.paypal_adapter",
        "PayPalPaymentProvider",
    ),
    "mercadopago": (
        "app.services.payment_providers.mercado_pago_adapter",
        "MercadoPagoPaymentProvider",
    ),
}


def get_payment_provider(
    provider_name: Optional[str] = None,
    *,
    config: Optional[Mapping[str, Any]] = None,
) -> PaymentProvider:
    """Return the configured provider adapter or fail with a clear safe error.

    `config` is injectable for tests. If omitted, Flask config is preferred; the
    environment is used only outside a Flask application context.
    """
    if config is None:
        try:
            from flask import current_app, has_app_context

            config = current_app.config if has_app_context() else {}
        except ImportError:
            config = {}

    selected = provider_name or config.get("PAYMENT_PROVIDER") or os.getenv(
        "PAYMENT_PROVIDER", "none"
    )
    selected = str(selected).strip().lower()

    if not selected or selected in {"none", "disabled", "off"}:
        raise PaymentProviderNotSelected(
            "Nenhum gateway de pagamento está selecionado. "
            "Defina PAYMENT_PROVIDER após a decisão do grupo."
        )

    adapter = PAYMENT_PROVIDER_ADAPTERS.get(selected)
    if adapter is None:
        raise UnsupportedPaymentProvider(
            "PAYMENT_PROVIDER deve ser 'paypal' ou 'mercadopago'."
        )

    module_name, class_name = adapter
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            raise PaymentProviderNotImplemented(
                f"O adaptador '{selected}' ainda não foi implementado; "
                "nenhum pagamento foi criado."
            ) from exc
        raise

    provider_class = getattr(module, class_name, None)
    if provider_class is None:
        raise PaymentProviderNotImplemented(
            f"O adaptador '{selected}' não expõe a classe {class_name}."
        )

    provider = provider_class.from_config(config)
    if not isinstance(provider, PaymentProvider):
        raise TypeError("O adaptador deve implementar PaymentProvider.")
    if provider.provider_name != selected:
        raise ValueError("O identificador do adaptador não corresponde à configuração.")
    return provider
