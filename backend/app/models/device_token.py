from app.database.database import db
from app.utils.datetime_utils import utc_now_naive


class DeviceToken(db.Model):
    """Push token linked to one authenticated CandyLand account."""

    __tablename__ = "device_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(512), nullable=False, unique=True, index=True)
    account_type = db.Column(db.String(20), nullable=False, index=True)
    account_id = db.Column(db.Integer, nullable=False, index=True)
    platform = db.Column(db.String(20), nullable=False, default="ANDROID")
    device_id = db.Column(db.String(120), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now_naive)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive)

    def to_dict(self):
        return {
            "id": self.id,
            "account_type": self.account_type,
            "account_id": self.account_id,
            "platform": self.platform,
            "active": bool(self.active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
