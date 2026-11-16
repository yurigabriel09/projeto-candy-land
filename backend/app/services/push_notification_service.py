"""FCM HTTP v1 sender. Push errors never roll back a committed order transition."""
import json
from pathlib import Path

import requests
from app.database.database import db
from app.models.device_token import DeviceToken
from flask import current_app, has_app_context
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from sqlalchemy.exc import SQLAlchemyError

_FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


class PushNotificationService:
    _credentials = None
    _credentials_path = None

    @staticmethod
    def _config():
        if not has_app_context():
            return None, None
        project_id = str(current_app.config.get("FCM_PROJECT_ID") or "").strip()
        service_file = str(current_app.config.get("FCM_SERVICE_ACCOUNT_FILE") or "").strip()
        return project_id, service_file

    @staticmethod
    def _resolve_service_file(service_file):
        configured = Path(service_file).expanduser()
        if configured.is_absolute():
            return configured
        backend_root = Path(__file__).resolve().parents[2]
        candidates = (Path.cwd() / configured, backend_root / configured)
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        return candidates[0].resolve()

    @classmethod
    def _access_token(cls, service_file):
        path = str(cls._resolve_service_file(service_file))
        if cls._credentials is None or cls._credentials_path != path:
            cls._credentials = service_account.Credentials.from_service_account_file(
                path, scopes=[_FCM_SCOPE]
            )
            cls._credentials_path = path
        if not cls._credentials.valid:
            cls._credentials.refresh(Request())
        return cls._credentials.token

    @staticmethod
    def _labels(status):
        return {
            "PENDENTE_PAGAMENTO": "Aguardando pagamento",
            "PAGAMENTO_CONFIRMADO": "Pagamento confirmado",
            "RESTAURANTE_RECEBEU": "Pedido recebido pela doceria",
            "RESTAURANTE_ACEITOU": "Pedido aceito",
            "PROCESSANDO": "Pedido em preparo",
            "PRONTO_PARA_ENTREGA": "Pedido pronto",
            "ENTREGUE": "Pedido entregue",
            "FINALIZADO": "Pedido finalizado",
            "CANCELADO": "Pedido cancelado",
        }.get(str(status or "").upper(), str(status or "Pedido atualizado"))

    @classmethod
    def notificar_pedido(
        cls, pedido, status_anterior=None, status_atual=None, tipo_evento="PEDIDO"
    ):
        """Notify customer and restaurant after a successful transaction commit."""
        if not pedido or not has_app_context():
            return {"sent": 0, "skipped": True}
        project_id, service_file = cls._config()
        if not project_id or not service_file or not cls._resolve_service_file(service_file).is_file():
            current_app.logger.info("FCM não configurado; evento de pedido não enviado.")
            return {"sent": 0, "skipped": True}

        try:
            targets = [
                ("PERSONAL", int(pedido.user_id)),
                ("BUSINESS", int(pedido.restaurant_id)),
            ]
            registrations = []
            for account_type, account_id in targets:
                registrations.extend(
                    DeviceToken.query.filter_by(
                        account_type=account_type, account_id=account_id, active=True
                    ).all()
                )
            if not registrations:
                return {"sent": 0, "skipped": True}

            access_token = cls._access_token(service_file)
            endpoint = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
            new_status = str(status_atual or pedido.status or "")
            delivery_labels = {
                "NAO_SOLICITADO": "Entrega ainda não solicitada",
                "PROCURANDO": "Procurando entregador",
                "MOTORISTA_ENCONTRADO": "Entregador encontrado",
                "MOTORISTA_A_CAMINHO": "Entregador a caminho da doceria",
                "MOTORISTA_NO_RESTAURANTE": "Entregador chegou à doceria",
                "PEDIDO_RETIRADO": "Pedido retirado pelo entregador",
                "EM_ROTA": "Pedido a caminho do endereço",
                "ENTREGA_CONCLUIDA": "Entrega concluída",
                "SEM_MOTORISTA": "Ainda não foi possível encontrar entregador",
                "CANCELADO": "Entrega cancelada",
            }
            status_label = (
                delivery_labels.get(new_status, new_status)
                if tipo_evento == "ENTREGA"
                else cls._labels(new_status)
            )
            sent = 0
            invalid_tokens = []
            for device in registrations:
                if device.account_type == "BUSINESS":
                    title = "Atualização da entrega" if tipo_evento == "ENTREGA" else "Atualização de pedido"
                    body = f"{pedido.order_code}: {status_label}."
                else:
                    title = "Sua entrega foi atualizada" if tipo_evento == "ENTREGA" else "Seu pedido mudou de status"
                    body = f"{pedido.order_code}: {status_label}."
                message = {
                    "message": {
                        "token": device.token,
                        "notification": {"title": title, "body": body},
                        "data": {
                            "order_id": str(pedido.id),
                            "order_code": str(pedido.order_code),
                            "status": new_status,
                            "order_status": str(pedido.status or ""),
                            "event_type": str(tipo_evento),
                            "previous_status": str(status_anterior or ""),
                            "account_type": device.account_type,
                        },
                        "android": {
                            "priority": "high",
                            "notification": {"channel_id": "candyland_orders"},
                        },
                    }
                }
                try:
                    response = requests.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {access_token}"},
                        json=message,
                        timeout=8,
                    )
                    if response.ok:
                        sent += 1
                        continue
                    try:
                        error_payload = response.json()
                    except ValueError:
                        error_payload = {}
                    error_text = json.dumps(error_payload, ensure_ascii=False)
                    current_app.logger.warning(
                        "FCM recusou token de dispositivo (HTTP %s): %s",
                        response.status_code,
                        error_text[:500],
                    )
                    if response.status_code == 404 or "UNREGISTERED" in error_text:
                        invalid_tokens.append(device)
                except requests.RequestException:
                    current_app.logger.exception("Falha de rede ao enviar notificação FCM.")

            for device in invalid_tokens:
                device.active = False
            if invalid_tokens:
                db.session.commit()
            return {"sent": sent, "invalid": len(invalid_tokens)}
        except Exception:
            # Notification transport must never change an already persisted order.
            current_app.logger.exception("Falha ao processar notificações do pedido %s.", getattr(pedido, "id", "?"))
            try:
                db.session.rollback()
            except SQLAlchemyError:
                pass
            return {"sent": 0, "error": True}
