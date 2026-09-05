from app.database.database import db

class ItemPedido(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True, index=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    id_produto = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    observacoes = db.Column(db.String(255), nullable=True)
    detalhes_personalizacao = db.Column(db.JSON, nullable=True)