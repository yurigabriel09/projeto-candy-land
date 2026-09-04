from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class Client(Base):
    __tablename__ = "clients"

    id_cliente = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    telefone = Column(String(20), unique=True, nullable=False)
    data_nascimento = Column(Date, nullable=True)
    status = Column(String(20), nullable=False)
    dt_criacao = Column(DateTime, nullable=False, default=datetime.utcnow)
    dt_atualizacao = Column(DateTime, nullable=True)