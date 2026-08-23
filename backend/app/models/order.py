from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="Pendente")  # Pendente, Processando, Concluido, Cancelado
    total = Column(Float, nullable=False)
    forma_pagamento = Column(String(50))  # PIX, Cartao, Boleto