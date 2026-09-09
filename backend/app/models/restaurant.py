from app.database.database import db

class Restaurante(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True, index=True)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    razao_social = db.Column(db.String(150), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, index=True, nullable=False)
    telefone = db.Column(db.String(20), unique=True, nullable=False)
    cpf_responsavel = db.Column(db.String(14), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), unique=True, nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "cnpj": self.cnpj,
            "razao_social": self.razao_social,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
            "cpf_responsavel": self.cpf_responsavel,
            "address_id": self.address_id,
            "ativo": self.ativo
        }