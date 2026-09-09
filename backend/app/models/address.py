from app.database.database import db

class Endereco(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True, index=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    id_restaurante = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=True)
    cep = db.Column(db.String(10), nullable=False)
    rua = db.Column(db.String(150), nullable=False)
    numero = db.Column(db.String(20), nullable=False)
    complemento = db.Column(db.String(100), nullable=True)
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    referencia = db.Column(db.String(150), nullable=True)
    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)
    tipo_endereco = db.Column(db.String(20), nullable=False)
    principal = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "id_usuario": self.id_usuario,
            "id_restaurante": self.id_restaurante,
            "cep": self.cep,
            "rua": self.rua,
            "numero": self.numero,
            "complemento": self.complemento,
            "bairro": self.bairro,
            "cidade": self.cidade,
            "estado": self.estado,
            "referencia": self.referencia,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "tipo_endereco": self.tipo_endereco,
            "principal": self.principal,
            "ativo": self.ativo
        }