from app.database.database import db

class Restaurante(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True, index=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, index=True, nullable=False)
    ativo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "ativo": self.ativo
        }