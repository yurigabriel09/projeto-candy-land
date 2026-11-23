from flask import Flask
import pytest
from app.database.database import db
from app.models.google_maps_route_usage import GoogleMapsRouteUsage
from app.services.google_routes_service import GoogleRoutesService


@pytest.fixture
def quota_app():
    app = Flask("google_routes_quota_test")
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        GOOGLE_MAPS_ROUTES_ENABLED=True,
        GOOGLE_MAPS_ROUTES_API_KEY="routes-test-key",
        GOOGLE_MAPS_ROUTES_MONTHLY_LIMIT=2,
        GOOGLE_MAPS_ROUTES_DAILY_LIMIT=10,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def test_quota_mensal_bloqueia_chamada_que_ultrapassa_limite(quota_app):
    with quota_app.app_context():
        GoogleRoutesService._reserve_quota()
        GoogleRoutesService._reserve_quota()
        with pytest.raises(ValueError, match="limite mensal"):
            GoogleRoutesService._reserve_quota()
        rows = GoogleMapsRouteUsage.query.all()
        monthly = next(row for row in rows if row.period_key.startswith("month:"))
        assert monthly.requests == 2


def test_quota_diaria_bloqueia_sem_consumir_contador_mensal(quota_app):
    with quota_app.app_context():
        quota_app.config["GOOGLE_MAPS_ROUTES_DAILY_LIMIT"] = 1
        GoogleRoutesService._reserve_quota()
        with pytest.raises(ValueError, match="limite diário"):
            GoogleRoutesService._reserve_quota()
        monthly = GoogleMapsRouteUsage.query.filter(GoogleMapsRouteUsage.period_key.like("month:%")).one()
        daily = GoogleMapsRouteUsage.query.filter(GoogleMapsRouteUsage.period_key.like("day:%")).one()
        assert monthly.requests == 1
        assert daily.requests == 1


def test_compute_routes_usa_somente_campos_essentials_e_nao_guarda_rota(quota_app, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"routes": [{"distanceMeters": 4820, "duration": "900s"}]}

    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append((url, json, headers, timeout))
        return FakeResponse()

    monkeypatch.setattr("app.services.google_routes_service.requests.post", fake_post)
    with quota_app.app_context():
        route = GoogleRoutesService.calcular_distancia(-23.55, -46.63, -23.57, -46.64)
        assert route["distance_km"] == 4.82
        assert route["duration_seconds"] == 900
        assert calls[0][2]["X-Goog-FieldMask"] == "routes.distanceMeters,routes.duration"
        assert calls[0][1]["routingPreference"] == "TRAFFIC_UNAWARE"
        # Somente os contadores de quota persistem; nenhuma rota ou coordenada é guardada.
        assert GoogleMapsRouteUsage.query.count() == 2
