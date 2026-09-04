from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, JSON
from app.database import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id_item_pedido = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("orders.id_order"), nullable=False)
    id_produto = Column(Integer, ForeignKey("products.id_product"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(DECIMAL(10, 2), nullable=False)
    observacoes = Column(String(255), nullable=True)
    detalhes_personalizacao = Column(JSON, nullable=True)