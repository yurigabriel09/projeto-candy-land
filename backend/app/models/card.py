from datetime import datetime
from app.database.database import db


class CartaoCliente(db.Model):
    """
    Guarda apenas a referencia tokenizada do cartao (gerada pelo gateway de
    pagamento) e os ultimos 4 digitos para exibicao. NUNCA armazenar numero
    completo do cartao ou CVV nesta tabela.

    Ainda nao ha integracao com gateway de pagamento no projeto - esta
    tabela deixa o modelo pronto para quando o fechamento de pedido /
    pagamento for implementado.
    """
    __tablename__ = "customer_cards"

    id = db.Column(db.Integer, primary_key=True, index=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    nome_titular = db.Column(db.String(120), nullable=False)
    bandeira = db.Column(db.String(30), nullable=False)
    ultimos_4_digitos = db.Column(db.String(4), nullable=False)
    mes_validade = db.Column(db.String(2), nullable=False)
    ano_validade = db.Column(db.String(4), nullable=False)

    # referencia opaca devolvida pelo gateway (ex.: Stripe/Pagar.me token)
    token_gateway = db.Column(db.String(255), nullable=False)

    cartao_principal = db.Column(db.Boolean, nullable=False, default=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    dt_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "id_cliente": self.id_cliente,
            "nome_titular": self.nome_titular,
            "bandeira": self.bandeira,
            "ultimos_4_digitos": self.ultimos_4_digitos,
            "mes_validade": self.mes_validade,
            "ano_validade": self.ano_validade,
            "cartao_principal": self.cartao_principal,
            "ativo": self.ativo,
            "dt_cadastro": self.dt_cadastro.isoformat() if self.dt_cadastro else None
            # token_gateway propositalmente omitido: dado sensivel, nunca
            # deve ir para o front-end.
        }
