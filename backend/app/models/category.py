from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from app.database import Base

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("restaurant_id", "name", name="uq_category_restaurant_name"),)

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    parent_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    icon_url = Column(String(255), nullable=True)
    cover_image_url = Column(String(255), nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)