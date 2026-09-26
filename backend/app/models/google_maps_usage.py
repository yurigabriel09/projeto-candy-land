from datetime import date, datetime
from sqlalchemy import UniqueConstraint
from app.database.database import db


class GoogleMapsUsage(db.Model):
    __tablename__ = "google_maps_usage"

    id = db.Column(db.Integer, primary_key=True)

    periodo = db.Column(db.String(7), nullable=False)
    sku = db.Column(db.String(100), nullable=False)

    limite_mensal = db.Column(db.Integer, nullable=False)
    limite_seguro = db.Column(db.Integer, nullable=False)

    consumido = db.Column(db.Integer, nullable=False, default=0)

    limite_diario = db.Column(db.Integer, nullable=False)
    usado_hoje = db.Column(db.Integer, nullable=False, default=0)

    data_controle_diario = db.Column(
        db.Date,
        nullable=False,
        default=date.today,
    )

    ultima_sincronizacao = db.Column(
        db.DateTime,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE",
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    atualizado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "periodo",
            "sku",
            name="uq_google_maps_usage_periodo_sku",
        ),
    )

    @property
    def saldo(self):
        return max(self.limite_seguro - self.consumido, 0)