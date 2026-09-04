from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, JSON
from app.database import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id_order_item = Column(Integer, primary_key=True, index=True)
    id_order = Column(Integer, ForeignKey("orders.id"), nullable=False)
    id_product = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    notes = Column(String(255), nullable=True)
    customization_details = Column(JSON, nullable=True)