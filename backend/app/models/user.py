from app.database.database import db

class Usuario(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, index=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    telefone = db.Column(db.String(20), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=db.func.now())
    atualizado_em = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())
    codigo_verificacao = db.Column(db.String(6), nullable=True)
    codigo_expira_em = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome_completo": self.nome_completo,
            "email": self.email,
            "telefone": self.telefone,
            "data_nascimento": self.data_nascimento.isoformat() if self.data_nascimento else None,
            "status": self.status,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None
        }