from datetime import datetime
from app.database.database import db


class Restaurante(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True, index=True)
    address_id = db.Column(
        db.Integer, db.ForeignKey("addresses.id"), unique=True, nullable=True
    )

    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    razao_social = db.Column(db.String(150), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    nome_responsavel = db.Column(db.String(150), nullable=True)
    cpf_responsavel = db.Column(db.String(14), nullable=False)
    email = db.Column(db.String(150), unique=True, index=True, nullable=False)
    telefone = db.Column(db.String(20), unique=True, nullable=False)

    descricao = db.Column(db.String(255), nullable=True)
    valor_minimo_pedido = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    taxa_entrega_base = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    raio_entrega_km = db.Column(db.Numeric(5, 2), nullable=True)
    horario_funcionamento = db.Column(db.String(120), nullable=True)

    # status operacional da doceria (EM_ANALISE, ABERTO, FECHADO, SUSPENSO)
    status = db.Column(db.String(20), nullable=False, default="EM_ANALISE")
    # controle administrativo (plataforma pode desativar a conta)
    ativo = db.Column(db.Boolean, default=True)
    dt_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "cnpj": self.cnpj,
            "razao_social": self.razao_social,
            "nome": self.nome,
            "nome_responsavel": self.nome_responsavel,
            "cpf_responsavel": self.cpf_responsavel,
            "email": self.email,
            "telefone": self.telefone,
            "descricao": self.descricao,
            "valor_minimo_pedido": (
                float(self.valor_minimo_pedido)
                if self.valor_minimo_pedido is not None else None
            ),
            "taxa_entrega_base": (
                float(self.taxa_entrega_base)
                if self.taxa_entrega_base is not None else None
            ),
            "raio_entrega_km": (
                float(self.raio_entrega_km)
                if self.raio_entrega_km is not None else None
            ),
            "horario_funcionamento": self.horario_funcionamento,
            "status": self.status,
            "ativo": self.ativo,
            "address_id": self.address_id,
            "dt_cadastro": self.dt_cadastro.isoformat() if self.dt_cadastro else None
        }
