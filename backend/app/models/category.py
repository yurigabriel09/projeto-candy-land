from datetime import datetime
from sqlalchemy import UniqueConstraint
from app.database.database import db

class Categoria(db.Model):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint(
            "id_restaurante",
            "nome",
            name="uq_categoria_restaurante_nome"
        ),
    )

    id = db.Column(db.Integer, primary_key=True, index=True)
    id_restaurante = db.Column(
        db.Integer,
        db.ForeignKey("restaurants.id"),
        nullable=False
    )
    id_categoria_pai = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=True
    )
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    url_icone = db.Column(db.String(255), nullable=True)
    url_capa = db.Column(db.String(255), nullable=True)
    ordem_exibicao = db.Column(db.Integer, nullable=False, default=0)
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    criada_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)