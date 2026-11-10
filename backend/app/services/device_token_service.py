from sqlalchemy.exc import SQLAlchemyError

from app.database.database import db
from app.models.device_token import DeviceToken


class DeviceTokenService:
    @staticmethod
    def registrar(token, account_id, account_type, platform="ANDROID", device_id=None):
        token = str(token or "").strip()
        platform = str(platform or "ANDROID").strip().upper()
        device_id = str(device_id or "").strip() or None
        if not token or len(token) > 512:
            return {"success": False, "erro": "Token FCM inválido.", "status_code": 400}
        if platform not in {"ANDROID", "IOS", "WEB"}:
            return {"success": False, "erro": "Plataforma inválida.", "status_code": 400}
        try:
            registro = DeviceToken.query.filter_by(token=token).first()
            if registro is None:
                registro = DeviceToken(token=token)
                db.session.add(registro)
            # Um token de aparelho pertence à sessão autenticada mais recente.
            registro.account_id = account_id
            registro.account_type = account_type
            registro.platform = platform
            registro.device_id = device_id
            registro.active = True
            db.session.commit()
            return {"success": True, "dados": registro.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Não foi possível registrar o dispositivo.", "status_code": 500}

    @staticmethod
    def remover(token, account_id, account_type):
        token = str(token or "").strip()
        if not token:
            return {"success": False, "erro": "Token FCM é obrigatório.", "status_code": 400}
        try:
            registro = DeviceToken.query.filter_by(
                token=token, account_id=account_id, account_type=account_type
            ).first()
            if registro:
                db.session.delete(registro)
                db.session.commit()
            return {"success": True}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Não foi possível remover o dispositivo.", "status_code": 500}
