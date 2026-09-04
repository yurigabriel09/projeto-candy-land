from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, ForeignKey, DateTime
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(String(255), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    is_available = Column(Boolean, default=True)
    is_imported = Column(Boolean, default=False)
    current_stock = Column(Integer, nullable=False, default=0)
    allows_customization = Column(Boolean, default=False)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)