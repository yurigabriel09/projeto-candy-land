from app.database.database import db


class EntregaPedido(db.Model):
    __tablename__ = "order_deliveries"

    id = db.Column(db.Integer, primary_key=True, index=True)
    pedido_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=False, unique=True
    )
    status = db.Column(db.String(30), nullable=False, default="NAO_SOLICITADO")
    iniciado_em = db.Column(db.DateTime, nullable=True)
    concluida_em = db.Column(db.DateTime, nullable=True)
    cancelada_em = db.Column(db.DateTime, nullable=True)

    pedido = db.relationship("Pedido", back_populates="entrega")
