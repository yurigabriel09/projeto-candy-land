"""Utilitários de data/hora usados pelos modelos SQLAlchemy."""

from datetime import UTC, datetime


def utc_now_naive() -> datetime:
    """Retorna UTC sem tzinfo para compatibilidade com colunas DateTime legadas.

    O valor representa UTC, embora o schema existente use DateTime sem timezone.
    Isso evita datetime.utcnow(), depreciado no Python 3.12+.
    """
    return datetime.now(UTC).replace(tzinfo=None)
