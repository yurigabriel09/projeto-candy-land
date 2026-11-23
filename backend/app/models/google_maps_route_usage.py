from app.database.database import db


class GoogleMapsRouteUsage(db.Model):
    """Contadores de quota; nunca armazena coordenadas ou resultados de rotas."""
    __tablename__ = "google_maps_route_usage"

    period_key = db.Column(db.String(32), primary_key=True)
    requests = db.Column(db.Integer, nullable=False, default=0)
