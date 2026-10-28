"""Select a payment-provider adapter without coupling order logic to a gateway."""
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
    "mock": (
        "app.services.payment_providers.mock_adapter",
        "MockPaymentProvider",
    ),
    "paypal": (
        "app.services.payment_providers.paypal_adapter",
        "PayPalPaymentProvider",
    ),
    "mercadopago": (
        "app.services.payment_providers.mercado_pago_adapter",
        "MercadoPagoPaymentProvider",
    ),
}
NON_PRODUCTION_ENVS = {"development", "dev", "local", "test", "testing"}


def get_payment_provider(
    provider_name: Optional[str] = None,
    *,
    config: Optional[Mapping[str, Any]] = None,
) -> PaymentProvider:
    """Return the configured adapter, failing closed when unavailable.

    The mock provider is explicitly forbidden in production, even when selected
    by environment variable. `config` is injectable to support isolated tests.
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

    if not selected or selected in {"none", "disabled", "off", "auto"}:
        raise PaymentProviderNotSelected(
            "Nenhum gateway de pagamento está selecionado. "
            "Defina PAYMENT_PROVIDER após a decisão do grupo."
        )

    if selected == "mock":
        environment = str(
            config.get("APP_ENV", os.getenv("APP_ENV", "production"))
        ).strip().lower()
        if environment not in NON_PRODUCTION_ENVS:
            raise UnsupportedPaymentProvider(
                "O provedor mock é permitido apenas em desenvolvimento/testes."
            )

    adapter = PAYMENT_PROVIDER_ADAPTERS.get(selected)
    if adapter is None:
        raise UnsupportedPaymentProvider(
            "PAYMENT_PROVIDER deve ser 'none', 'mock', 'paypal' ou 'mercadopago'."
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
