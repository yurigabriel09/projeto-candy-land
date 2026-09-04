from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL
from app.database import Base

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    zip_code = Column(String(10), nullable=False)
    street = Column(String(150), nullable=False)
    number = Column(String(20), nullable=False)
    complement = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    reference = Column(String(150), nullable=True)
    latitude = Column(DECIMAL(9, 6), nullable=True)
    longitude = Column(DECIMAL(9, 6), nullable=True)
    address_type = Column(String(20), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)