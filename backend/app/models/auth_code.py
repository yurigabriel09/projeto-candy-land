from app.database.database import db

class CodigoAutenticacao(db.Model):
    __tablename__ = "auth_codes"

    id = db.Column(db.Integer, primary_key=True, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    restaurante_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=True)
    tipo = db.Column(db.String(20), nullable=False)
    destino = db.Column(db.String(150), nullable=False)
    codigo_hash = db.Column(db.String(255), nullable=False)
    expira_em = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "restaurante_id": self.restaurante_id,
            "tipo": self.tipo,
            "destino": self.destino,
            "expira_em": self.expira_em.isoformat() if self.expira_em else None,
            "usado": self.usado,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None
        }