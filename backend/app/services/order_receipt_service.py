"""Customer receipt PIN issuance and restaurant-side verification."""
import hashlib
import hmac
import re

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.database.database import db
from app.models.order import Pedido
from app.models.order_receipt_code import OrderReceiptCode
from app.services.order_workflow_service import (
    OrderTransitionError,
    validar_transicao_pedido,
)
from app.utils.datetime_utils import utc_now_naive


MAX_FAILED_ATTEMPTS = 5
STATUSES_WITH_PAID_ORDER = {
    "PAGAMENTO_CONFIRMADO", "RESTAURANTE_RECEBEU", "RESTAURANTE_ACEITOU",
    "PROCESSANDO", "PRONTO_PARA_ENTREGA", "ENTREGUE",
}


class OrderReceiptService:
    @staticmethod
    def _secret() -> bytes:
        return str(current_app.config.get("SECRET_KEY") or "").encode("utf-8")

    @staticmethod
    def _derive_code(pedido: Pedido, generation: int) -> str:
        message = f"candyland-receipt:{pedido.id}:{pedido.order_code}:{generation}".encode("utf-8")
        digest = hmac.new(OrderReceiptService._secret(), message, hashlib.sha256).digest()
        return f"{int.from_bytes(digest[:4], 'big') % 1_000_000:06d}"

    @staticmethod
    def _hash_code(order_id: int, code: str) -> str:
        value = f"candyland-receipt-verify:{order_id}:{code}".encode("utf-8")
        return hmac.new(OrderReceiptService._secret(), value, hashlib.sha256).hexdigest()

    @staticmethod
    def emitir_codigo(pedido_id: int, account_id: int, account_type: str):
        if account_type != "PERSONAL":
            return {"success": False, "erro": "Somente o cliente pode consultar o código de recebimento.", "status_code": 403}
        pedido = db.session.get(Pedido, pedido_id)
        if not pedido:
            return {"success": False, "erro": "Pedido não encontrado.", "status_code": 404}
        if pedido.user_id != account_id:
            return {"success": False, "erro": "Você não tem acesso a este pedido.", "status_code": 403}
        if pedido.status not in STATUSES_WITH_PAID_ORDER:
            return {"success": False, "erro": "O código fica disponível depois que o pagamento é confirmado e antes de finalizar a entrega/retirada.", "status_code": 409}

        try:
            registro = OrderReceiptCode.query.filter_by(order_id=pedido.id).first()
            if registro and registro.used_at is not None:
                return {"success": False, "erro": "O recebimento deste pedido já foi confirmado.", "status_code": 409}
            rotated_after_lock = False
            if registro is None:
                registro = OrderReceiptCode(order_id=pedido.id, generation=1, failed_attempts=0, code_hash="")
                db.session.add(registro)
                db.session.flush()
            elif registro.failed_attempts >= MAX_FAILED_ATTEMPTS:
                # A new derived code is issued only after the old code is locked.
                registro.generation += 1
                registro.failed_attempts = 0
                rotated_after_lock = True

            code = OrderReceiptService._derive_code(pedido, registro.generation)
            expected_hash = OrderReceiptService._hash_code(pedido.id, code)
            if not hmac.compare_digest(str(registro.code_hash or ""), expected_hash):
                # Also recovers safely if SECRET_KEY has changed since issuance.
                # Don't advance twice when this request already rotated a locked code.
                if registro.code_hash and not rotated_after_lock:
                    registro.generation += 1
                    code = OrderReceiptService._derive_code(pedido, registro.generation)
                    expected_hash = OrderReceiptService._hash_code(pedido.id, code)
                registro.code_hash = expected_hash
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Código de recebimento disponível. Compartilhe somente na entrega/retirada do pedido.",
                "codigo": code,
                "pedido_id": pedido.id,
                "tentativas_restantes": MAX_FAILED_ATTEMPTS - registro.failed_attempts,
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Não foi possível emitir o código de recebimento.", "status_code": 500}

    @staticmethod
    def confirmar_recebimento(pedido_id: int, account_id: int, account_type: str, codigo: str):
        if account_type != "BUSINESS":
            return {"success": False, "erro": "Somente o restaurante responsável pode confirmar o recebimento.", "status_code": 403}
        pedido = db.session.get(Pedido, pedido_id)
        if not pedido:
            return {"success": False, "erro": "Pedido não encontrado.", "status_code": 404}
        if pedido.restaurant_id != account_id:
            return {"success": False, "erro": "Você não administra este pedido.", "status_code": 403}
        if pedido.status in {"CANCELADO", "FINALIZADO"}:
            return {"success": False, "erro": "O pedido já está encerrado ou cancelado.", "status_code": 409}
        if pedido.order_type == "PICKUP" and pedido.status != "PRONTO_PARA_ENTREGA":
            return {"success": False, "erro": "A retirada só pode ser finalizada quando o pedido estiver pronto para retirada.", "status_code": 409}
        if pedido.order_type == "DELIVERY" and pedido.status != "ENTREGUE":
            return {"success": False, "erro": "Para entrega, primeiro registre a conclusão logística; depois valide o código do destinatário.", "status_code": 409}

        codigo = str(codigo or "").strip()
        if not re.fullmatch(r"\d{6}", codigo):
            return {"success": False, "erro": "Informe o código de recebimento com seis dígitos.", "status_code": 400}

        try:
            registro = OrderReceiptCode.query.filter_by(order_id=pedido.id).first()
            if not registro or not registro.code_hash:
                return {"success": False, "erro": "O cliente ainda não gerou o código de recebimento.", "status_code": 409}
            if registro.used_at is not None:
                return {"success": False, "erro": "Este código já foi utilizado.", "status_code": 409}
            if registro.failed_attempts >= MAX_FAILED_ATTEMPTS:
                return {"success": False, "erro": "Código bloqueado após muitas tentativas. Peça ao cliente para gerar um novo código.", "status_code": 429}

            expected = OrderReceiptService._hash_code(pedido.id, codigo)
            if not hmac.compare_digest(str(registro.code_hash), expected):
                registro.failed_attempts += 1
                db.session.commit()
                blocked = registro.failed_attempts >= MAX_FAILED_ATTEMPTS
                return {
                    "success": False,
                    "erro": "Código incorreto. Peça ao cliente para conferir o código." if not blocked else "Código bloqueado após cinco tentativas. Peça ao cliente para gerar um novo código.",
                    "status_code": 429 if blocked else 400,
                }

            if pedido.order_type == "PICKUP":
                validar_transicao_pedido(pedido.status, "ENTREGUE")
                pedido.status = "ENTREGUE"
                pedido.delivered_at = utc_now_naive()
            validar_transicao_pedido(pedido.status, "FINALIZADO")
            pedido.status = "FINALIZADO"
            if pedido.delivered_at is None:
                pedido.delivered_at = utc_now_naive()
            registro.used_at = utc_now_naive()
            db.session.commit()
            return {"success": True, "mensagem": "Recebimento confirmado; pedido finalizado.", "pedido": OrderReceiptService._pedido_dict(pedido)}
        except OrderTransitionError as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 409}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao finalizar o pedido.", "status_code": 500}

    @staticmethod
    def _pedido_dict(pedido):
        # Share the canonical order representation used across the API.
        from app.services.order_service import OrderService
        return OrderService._to_dict(pedido)
