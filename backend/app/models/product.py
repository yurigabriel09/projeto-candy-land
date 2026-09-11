from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, ForeignKey, DateTime
from app.database.database import db

class Produto(db.Model):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(String(255), nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    is_imported = Column(Boolean, default=False, nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    allows_customization = Column(Boolean, default=False, nullable=False)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_produto": self.id,
            "id_restaurante": self.restaurant_id,
            "id_categoria": self.category_id,
            "nome_produto": self.name,
            "descricao_produto": self.description,
            "preco_produto": float(self.price) if self.price is not None else None,
            "produto_disponivel": self.is_available,
            "produto_importado": self.is_imported,
            "qtd_estoque": self.current_stock,
            "permite_personalizacao": self.allows_customization,
            "imagem_url": self.image_url,
            "dt_cadastro": self.created_at.isoformat() if self.created_at else None,
            "dt_atualizacao": self.updated_at.isoformat() if self.updated_at else None
        }