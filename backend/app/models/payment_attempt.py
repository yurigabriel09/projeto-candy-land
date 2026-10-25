"""Persistent payment attempt metadata.

This table stores normalized fields only; provider payloads and card data are
never persisted. The initial MVP allows one attempt per order, which makes
retries idempotent while the UI and gateway-retry policy are being defined.
"""
from sqlalchemy import Column, DECIMAL, DateTime, ForeignKey, Integer, String

from app.database.database import db
from app.utils.datetime_utils import utc_now_naive


class PaymentAttempt(db.Model):
    __tablename__ = "payment_attempts"

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    provider = Column(String(30), nullable=False)
    provider_payment_id = Column(String(160), nullable=False, unique=True)
    idempotency_key = Column(String(200), nullable=False, unique=True)
    payment_method = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING", index=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="BRL")
    approval_url = Column(String(1000), nullable=True)
    pix_copy_paste = Column(String(2000), nullable=True)
    pix_qr_code_base64 = Column(String(8000), nullable=True)
    boleto_url = Column(String(1000), nullable=True)
    boleto_line = Column(String(200), nullable=True)
    message = Column(String(500), nullable=True)
    # Last processed event is a lightweight duplicate guard; provider event
    # history and auditable financial ledger remain future work.
    last_event_id = Column(String(180), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    updated_at = Column(
        DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive
    )
