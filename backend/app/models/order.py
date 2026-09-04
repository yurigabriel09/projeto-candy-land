from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id_pedido = Column(Integer, primary_key=True, index=True)
    codigo_pedido = Column(String(20), unique=True, nullable=False)
    id_cliente = Column(Integer, ForeignKey("clients.id_cliente"), nullable=False)
    id_doceria = Column(Integer, ForeignKey("restaurants.id_restaurante"), nullable=False)
    id_endereco_entrega = Column(Integer, ForeignKey("addresses.id_endereco"), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    desconto = Column(DECIMAL(10, 2), default=0)
    taxa_entrega = Column(DECIMAL(10, 2), default=0)
    taxa_plataforma = Column(DECIMAL(10, 2), default=0)
    total = Column(DECIMAL(10, 2), nullable=False)
    tipo_pedido = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False)
    forma_pagamento = Column(String(30), nullable=False)
    observacao_geral = Column(String(255), nullable=True)
    data_pedido = Column(DateTime, nullable=False)
    previsao_entrega = Column(DateTime, nullable=True)
    data_entrega = Column(DateTime, nullable=True)