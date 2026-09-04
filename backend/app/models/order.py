from datetime import datetime
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    delivery_address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    discount = Column(DECIMAL(10, 2), nullable=False, default=0)
    delivery_fee = Column(DECIMAL(10, 2), nullable=False, default=0)
    platform_fee = Column(DECIMAL(10, 2), nullable=False, default=0)
    total = Column(DECIMAL(10, 2), nullable=False)
    order_type = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False, default="CREATED")
    payment_method = Column(String(30), nullable=False)
    general_note = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    estimated_delivery_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)