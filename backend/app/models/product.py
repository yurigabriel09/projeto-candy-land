from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, ForeignKey
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id_produto = Column(Integer, primary_key=True, index=True)
    id_restaurante = Column(Integer, ForeignKey("restaurants.id_restaurante"), nullable=False)
    id_categoria = Column(Integer, ForeignKey("categories.id_categoria"), nullable=False)
    nome = Column(String(120), nullable=False)
    descricao = Column(String(255), nullable=False)
    preco = Column(DECIMAL(10, 2), nullable=False)
    disponivel = Column(Boolean, default=True)
    is_importado = Column(Boolean, default=False)
    estoque_atual = Column(Integer, nullable=False)
    permite_personalizacao = Column(Boolean, default=False)
    imagem_url = Column(String(255), nullable=True)
    dt_cadastro = Column(DateTime, nullable=False)
    dt_atualizacao = Column(DateTime, nullable=True)