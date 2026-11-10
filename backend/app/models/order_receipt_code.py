"""Hash-only confirmation code used to finalize order handover.

The customer can retrieve the same derived code while the order is active; the
raw code is never stored in the database.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.database.database import db
from app.utils.datetime_utils import utc_now_naive


class OrderReceiptCode(db.Model):
    __tablename__ = "order_receipt_codes"

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    code_hash = Column(String(64), nullable=False)
    generation = Column(Integer, nullable=False, default=1)
    failed_attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    used_at = Column(DateTime, nullable=True)
