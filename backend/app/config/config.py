import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

_TRUTHY_VALUES = {"true", "1", "yes", "on"}
_AMBIENTES_NAO_PRODUTIVOS = {"development", "dev", "local", "test", "testing"}


def _valor_verdadeiro(valor):
    if isinstance(valor, bool):
        return valor
    return str(valor or "").strip().lower() in _TRUTHY_VALUES


def telefone_compartilhado_permitido(config):
    """Permite reutilizar telefone somente em ambientes explicitamente não produtivos.

    A variável ALLOW_DUPLICATE_PHONE sozinha nunca habilita a regra em produção.
    O APP_ENV ausente assume production para privilegiar comportamento seguro.
    """
    ambiente = str(config.get("APP_ENV", "production")).strip().lower()
    if ambiente not in _AMBIENTES_NAO_PRODUTIVOS:
        return False

    return _valor_verdadeiro(config.get("ALLOW_DUPLICATE_PHONE", False))


def autoaprovacao_restaurante_teste_permitida(config):
    """Permite abrir lojas EM_ANALISE apenas em ambiente não produtivo.

    A opção existe para validar o fluxo de compra localmente. Em produção,
    a aprovação administrativa continua obrigatória mesmo que a variável
    ALLOW_BUSINESS_SELF_APPROVAL_FOR_TESTS esteja definida como true.
    """
    ambiente = str(config.get("APP_ENV", "production")).strip().lower()
    if ambiente not in _AMBIENTES_NAO_PRODUTIVOS:
        return False

    return _valor_verdadeiro(
        config.get("ALLOW_BUSINESS_SELF_APPROVAL_FOR_TESTS", True)
    )


class Config:
    APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOW_DUPLICATE_PHONE = telefone_compartilhado_permitido(
        {
            "APP_ENV": APP_ENV,
            "ALLOW_DUPLICATE_PHONE": os.getenv("ALLOW_DUPLICATE_PHONE", "false"),
        }
    )
    ALLOW_BUSINESS_SELF_APPROVAL_FOR_TESTS = autoaprovacao_restaurante_teste_permitida(
        {
            "APP_ENV": APP_ENV,
            "ALLOW_BUSINESS_SELF_APPROVAL_FOR_TESTS": os.getenv(
                "ALLOW_BUSINESS_SELF_APPROVAL_FOR_TESTS", "true"
            ),
        }
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-troque-em-producao")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    GOOGLE_CLOCK_SKEW_SECONDS = int(os.getenv("GOOGLE_CLOCK_SKEW_SECONDS", "300"))
    # Checkout Pro do Mercado Pago. O Access Token e o segredo de webhook ficam no backend.
    PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "none").strip().lower()
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    MERCADO_PAGO_ACCESS_TOKEN = os.getenv("MERCADO_PAGO_ACCESS_TOKEN", "").strip()
    MERCADO_PAGO_WEBHOOK_SECRET = os.getenv("MERCADO_PAGO_WEBHOOK_SECRET", "").strip()
    MERCADO_PAGO_NOTIFICATION_URL = os.getenv("MERCADO_PAGO_NOTIFICATION_URL", "").strip()
    MERCADO_PAGO_RETURN_URL_BASE = os.getenv(
        "MERCADO_PAGO_RETURN_URL_BASE", FRONTEND_URL
    ).strip().rstrip("/")
    MERCADO_PAGO_SANDBOX = _valor_verdadeiro(
        os.getenv("MERCADO_PAGO_SANDBOX", "true")
    )
    # PayPal Orders v2; segredos somente no backend. Sandbox é o padrão.
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "").strip()
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
    PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox").strip().lower()
    PAYPAL_API_BASE = os.getenv("PAYPAL_API_BASE", "").strip()
    PAYPAL_WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID", "").strip()
    PAYPAL_RETURN_URL_BASE = os.getenv("PAYPAL_RETURN_URL_BASE", FRONTEND_URL).strip().rstrip("/")
    # Chave restrita à API Geocoding, mantida apenas no backend.
    GOOGLE_MAPS_GEOCODING_API_KEY = os.getenv("GOOGLE_MAPS_GEOCODING_API_KEY", "").strip()
    # Routes usa a mesma chave de servidor por padrão, mas só é ativada quando a chave existe.
    GOOGLE_MAPS_ROUTES_API_KEY = (os.getenv("GOOGLE_MAPS_ROUTES_API_KEY") or GOOGLE_MAPS_GEOCODING_API_KEY).strip()
    GOOGLE_MAPS_ROUTES_ENABLED = _valor_verdadeiro(
        os.getenv("GOOGLE_MAPS_ROUTES_ENABLED", "true" if GOOGLE_MAPS_ROUTES_API_KEY else "false")
    )
    # Limites internos conservadores; o serviço impõe hard caps de 4.000/mês e 100/dia.
    GOOGLE_MAPS_ROUTES_MONTHLY_LIMIT = int(os.getenv("GOOGLE_MAPS_ROUTES_MONTHLY_LIMIT", "4000"))
    GOOGLE_MAPS_ROUTES_DAILY_LIMIT = int(os.getenv("GOOGLE_MAPS_ROUTES_DAILY_LIMIT", "100"))
    # Firebase Cloud Messaging HTTP v1; a chave de serviço permanece somente no backend.
    FCM_PROJECT_ID = os.getenv("FCM_PROJECT_ID", "").strip()
    FCM_SERVICE_ACCOUNT_FILE = os.getenv("FCM_SERVICE_ACCOUNT_FILE", "").strip()

    UPLOAD_FOLDER = BASE_DIR / "uploads"
    UPLOAD_MAX_BYTES = 2 * 1024 * 1024
    # Limite duro da requisição (folga para o overhead do multipart)
    MAX_CONTENT_LENGTH = UPLOAD_MAX_BYTES + 512 * 1024
