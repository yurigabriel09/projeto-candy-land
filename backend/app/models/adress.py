from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL
from app.database import Base

class Address(Base):
    __tablename__ = "addresses"

    id_endereco = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clients.id_cliente"), nullable=False)
    cep = Column(String(10), nullable=False)
    logradouro = Column(String(150), nullable=False)
    numero = Column(String(20), nullable=False)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    referencia = Column(String(150), nullable=True)
    latitude = Column(DECIMAL(9, 6), nullable=True)
    longitude = Column(DECIMAL(9, 6), nullable=True)
    tipo_endereco = Column(String(20), nullable=False)
    principal = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)