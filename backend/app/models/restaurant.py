from datetime import datetime
from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime
from app.database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False, unique=True)
    trade_name = Column(String(120), nullable=False)
    legal_name = Column(String(150), nullable=True)
    cnpj = Column(String(18), unique=True, nullable=False)
    responsible_name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)
    minimum_order_value = Column(DECIMAL(10, 2), nullable=False, default=0)
    base_delivery_fee = Column(DECIMAL(10, 2), nullable=False, default=0)
    delivery_radius_km = Column(DECIMAL(5, 2), nullable=False)
    operating_hours = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)