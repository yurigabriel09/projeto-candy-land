"""Integração econômica e limitada com Google Routes API.

Não persistimos distância/duração retornada pelo Google. Os resultados são
usados somente durante a cotação/criação do pedido. A tabela de quota registra
apenas contadores de consumo, sem conteúdo de rota ou coordenadas.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone

import requests
from flask import current_app
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database.database import db
from app.models.google_maps_route_usage import GoogleMapsRouteUsage

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
HARD_MONTHLY_LIMIT = 4000
HARD_DAILY_LIMIT = 100


class GoogleRoutesService:
    @staticmethod
    def _enabled() -> bool:
        return bool(current_app.config.get("GOOGLE_MAPS_ROUTES_ENABLED", False))

    @staticmethod
    def _reserve_quota() -> None:
        """Reserva uma chamada atomicamente, inclusive em múltiplos workers."""
        config = current_app.config
        monthly_limit = min(
            max(1, int(config.get("GOOGLE_MAPS_ROUTES_MONTHLY_LIMIT", 4000))),
            HARD_MONTHLY_LIMIT,
        )
        daily_limit = min(
            max(1, int(config.get("GOOGLE_MAPS_ROUTES_DAILY_LIMIT", 100))),
            HARD_DAILY_LIMIT,
        )
        now = datetime.now(timezone.utc)
        periods = (
            (f"month:{now:%Y-%m}", monthly_limit, "limite mensal interno de 4.000 rotas"),
            (f"day:{now:%Y-%m-%d}", daily_limit, "limite diário interno de 100 rotas"),
        )
        table = GoogleMapsRouteUsage.__table__
        dialect = db.engine.dialect.name
        if dialect == "sqlite":
            insert_factory = sqlite_insert
        elif dialect == "postgresql":
            insert_factory = pg_insert
        else:
            raise ValueError("O controle de consumo de rotas exige SQLite ou PostgreSQL.")

        try:
            # As duas reservas pertencem à mesma transação: se uma cota falhar,
            # nenhuma das duas é contabilizada.
            for period_key, limit, label in periods:
                statement = insert_factory(table).values(period_key=period_key, requests=1)
                statement = statement.on_conflict_do_update(
                    index_elements=[table.c.period_key],
                    set_={"requests": table.c.requests + 1},
                    where=table.c.requests < limit,
                ).returning(table.c.requests)
                reserved = db.session.execute(statement).scalar_one_or_none()
                if reserved is None:
                    db.session.rollback()
                    raise ValueError(
                        f"A consulta de rota foi bloqueada pelo {label}. "
                        "A entrega com rota precisa aguardar a renovação da cota; retirada continua disponível."
                    )
            db.session.commit()
        except ValueError:
            raise
        except Exception as exc:  # fail closed: nunca chamar Google sem reservar quota
            db.session.rollback()
            raise ValueError(
                "Não foi possível validar o limite de consumo de mapas. "
                "Por segurança, o cálculo de entrega foi interrompido."
            ) from exc

    @staticmethod
    def calcular_distancia(
        origem_lat: float,
        origem_lng: float,
        destino_lat: float,
        destino_lng: float,
    ) -> dict | None:
        """Retorna a rota atual sem guardar o conteúdo fornecido pelo Google.

        Quando a integração estiver desativada, retorna None para manter o
        comportamento legado por linha reta. Quando estiver ativada, falhas de
        API/quota interrompem a cotação em vez de cobrar um frete incorreto.
        """
        if not GoogleRoutesService._enabled():
            return None

        api_key = str(current_app.config.get("GOOGLE_MAPS_ROUTES_API_KEY", "") or "").strip()
        if not api_key:
            raise ValueError(
                "A API Routes está habilitada no CandyLand, mas GOOGLE_MAPS_ROUTES_API_KEY não foi configurada."
            )

        GoogleRoutesService._reserve_quota()
        payload = {
            "origin": {"location": {"latLng": {"latitude": origem_lat, "longitude": origem_lng}}},
            "destination": {"location": {"latLng": {"latitude": destino_lat, "longitude": destino_lng}}},
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_UNAWARE",
            "computeAlternativeRoutes": False,
            "languageCode": "pt-BR",
            "units": "METRIC",
        }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            # Só pedimos distância e duração: sem polylines, tráfego ou campos Pro.
            "X-Goog-FieldMask": "routes.distanceMeters,routes.duration",
        }
        try:
            response = requests.post(ROUTES_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            body = response.json()
        except requests.Timeout as exc:
            raise ValueError("O cálculo de rota demorou demais. Tente novamente ou escolha retirada.") from exc
        except (requests.RequestException, ValueError) as exc:
            # Não imprimir chave nem corpo bruto do Google no log/resposta.
            raise ValueError(
                "Não foi possível calcular a rota pelo Google. Confira as restrições da chave e a ativação da Routes API."
            ) from exc

        routes = body.get("routes") if isinstance(body, dict) else None
        if not routes:
            raise ValueError("O Google não encontrou uma rota de carro para este endereço.")
        route = routes[0]
        try:
            distance_meters = float(route["distanceMeters"])
            duration_text = str(route["duration"])
            duration_match = re.fullmatch(r"(\d+(?:\.\d+)?)s", duration_text)
            if not duration_match:
                raise ValueError("Duração de rota inválida.")
            duration_seconds = int(math.ceil(float(duration_match.group(1))))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("O Google retornou dados de rota incompletos.") from exc

        if not math.isfinite(distance_meters) or distance_meters <= 0 or duration_seconds < 0:
            raise ValueError("O Google retornou uma distância ou duração inválida.")

        return {
            "distance_km": round(distance_meters / 1000.0, 2),
            "distance_km_raw": distance_meters / 1000.0,
            "duration_seconds": duration_seconds,
            "source": "GOOGLE_ROUTES_ESSENTIALS",
        }
