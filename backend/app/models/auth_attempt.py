import uuid
from app.database.database import db

class TentativaAutenticacao(db.Model):
    __tablename__ = "auth_attempts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canal_inicial = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email_validado = db.Column(db.Boolean, nullable=False, default=False)
    telefone_validado = db.Column(db.Boolean, nullable=False, default=False)
    concluida = db.Column(db.Boolean, nullable=False, default=False)
    expira_em = db.Column(db.DateTime, nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "canal_inicial": self.canal_inicial,
            "email": self.email,
            "telefone": self.telefone,
            "email_validado": self.email_validado,
            "telefone_validado": self.telefone_validado,
            "concluida": self.concluida,
            "expira_em": self.expira_em.isoformat() if self.expira_em else None,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None
        }