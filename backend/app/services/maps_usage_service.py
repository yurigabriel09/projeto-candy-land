from datetime import date, datetime

from sqlalchemy import select

from app.database.database import db
from app.models.google_maps_usage import GoogleMapsUsage


DEFAULT_MONTHLY_LIMIT = 10000
DEFAULT_SAFE_LIMIT = 9000
DEFAULT_DAILY_LIMIT = 300


class MapsUsageLimitExceeded(Exception):
    """Indica que o limite interno de uso do Google Maps foi atingido."""


def _current_period():
    return date.today().strftime("%Y-%m")


def _get_usage(sku):
    periodo = _current_period()

    usage = db.session.execute(
        select(GoogleMapsUsage).where(
            GoogleMapsUsage.periodo == periodo,
            GoogleMapsUsage.sku == sku,
        )
    ).scalar_one_or_none()

    if usage:
        return usage

    usage = GoogleMapsUsage(
        periodo=periodo,
        sku=sku,
        limite_mensal=DEFAULT_MONTHLY_LIMIT,
        limite_seguro=DEFAULT_SAFE_LIMIT,
        consumido=0,
        limite_diario=DEFAULT_DAILY_LIMIT,
        usado_hoje=0,
        status="ACTIVE",
        ultima_sincronizacao=datetime.utcnow(),
    )

    db.session.add(usage)
    db.session.flush()

    return usage

def _reset_daily_usage_if_needed(usage):
    today = date.today()

    if usage.data_controle_diario != today:
        usage.data_controle_diario = today
        usage.usado_hoje = 0
        usage.atualizado_em = datetime.utcnow()
        db.session.flush()

def can_consume(sku, quantidade=1):
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    usage = _get_usage(sku)
    _reset_daily_usage_if_needed(usage)

    if usage.status != "ACTIVE":
        return False

    if usage.consumido + quantidade > usage.limite_seguro:
        return False

    if usage.usado_hoje + quantidade > usage.limite_diario:
        return False

    return True


def consume(sku, quantidade=1):
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    usage = _get_usage(sku)
    _reset_daily_usage_if_needed(usage)

    if usage.status != "ACTIVE":
        raise MapsUsageLimitExceeded(
            f"O uso do Google Maps para '{sku}' está bloqueado."
        )

    if usage.consumido + quantidade > usage.limite_seguro:
        usage.status = "BLOCKED"
        db.session.commit()

        raise MapsUsageLimitExceeded(
            f"O limite mensal seguro de '{sku}' foi atingido."
        )

    if usage.usado_hoje + quantidade > usage.limite_diario:
        raise MapsUsageLimitExceeded(
            f"O limite diário de '{sku}' foi atingido."
        )

    usage.consumido += quantidade
    usage.usado_hoje += quantidade
    usage.atualizado_em = datetime.utcnow()

    if usage.consumido >= usage.limite_seguro:
        usage.status = "BLOCKED"

    db.session.commit()

    return usage


def get_usage(sku):
    return _get_usage(sku)