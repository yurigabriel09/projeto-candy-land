from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey
from app.database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id_restaurante = Column(Integer, primary_key=True, index=True)
    id_endereco = Column(Integer, ForeignKey("adresses.id_endereco"), nullable=False, unique=True)
    nome_fantasia = Column(String(120), nullable=False)
    razao_social = Column(String(150), nullable=True)
    cnpj = Column(String(18), unique=True, nullable=False)
    nome_responsavel = Column(String(120), nullable=False)
    telefone = Column(String(20), nullable=False)
    email = Column(String(150), nullable=False)
    descricao = Column(String(255), nullable=True)
    valor_minimo_pedido = Column(DECIMAL(10, 2), nullable=False)
    taxa_entrega_base = Column(DECIMAL(10, 2), nullable=False)
    raio_entrega_km = Column(DECIMAL(5, 2), nullable=False)
    horario_funcionamento = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False)
    dt_cadastro = Column(DateTime, nullable=False)