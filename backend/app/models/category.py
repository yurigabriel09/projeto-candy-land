from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id_categoria = Column(Integer, primary_key=True, index=True)
    id_doceria = Column(Integer, ForeignKey("restaurants.id_restaurante"), nullable=False)
    id_categoria_pai = Column(Integer, ForeignKey("categories.id_categoria"), nullable=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255), nullable=True)
    icone_url = Column(String(255), nullable=True)
    imagem_capa_url = Column(String(255), nullable=True)
    ordem_exibicao = Column(Integer, nullable=False)
    ativa = Column(Boolean, default=True)
    dt_cadastro = Column(DateTime, nullable=False)