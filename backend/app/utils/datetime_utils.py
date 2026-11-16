"""Utilitários de data/hora usados pelos modelos SQLAlchemy e pelos relatórios."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Horário de Brasília. O banco guarda UTC "naive" (sem tzinfo); toda regra de
# negócio baseada em "hoje", "semana" ou "mês" deve usar este fuso.
BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")


def utc_now_naive() -> datetime:
    """Retorna UTC sem tzinfo para compatibilidade com colunas DateTime legadas.

    O valor representa UTC, embora o schema existente use DateTime sem timezone.
    Isso evita datetime.utcnow(), depreciado no Python 3.12+.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def agora_brasilia() -> datetime:
    """Data/hora atual com tzinfo de Brasília."""
    return datetime.now(BRASILIA_TZ)


def inicio_do_dia_brasilia(dt: datetime | None = None) -> datetime:
    """00:00 (Brasília) do dia de `dt` (padrão: agora)."""
    dt = dt or agora_brasilia()
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def brasilia_para_utc_naive(dt: datetime) -> datetime:
    """Converte um datetime de Brasília (aware) para UTC naive, como no banco."""
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def utc_naive_para_brasilia(dt: datetime) -> datetime:
    """Converte um datetime UTC naive (do banco) para Brasília (aware)."""
    return dt.replace(tzinfo=timezone.utc).astimezone(BRASILIA_TZ)
