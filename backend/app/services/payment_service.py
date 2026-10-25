"""Payment orchestration shared by the mock now and real adapters later."""
from decimal import Decimal
from typing import Any, Dict, Optional

from flask import current_app, has_app_context
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database.database import db
from app.models.order import Pedido
from app.models.payment_attempt import PaymentAttempt
from app.services.order_service import OrderService
from app.services.payment_providers.contracts import (
    CreatePaymentCommand,
    PaymentMethod,
    PaymentProviderError,
    PaymentStatus,
)
from app.services.payment_providers.factory import (
    NON_PRODUCTION_ENVS,
    get_payment_provider,
)


class PaymentService:
    @staticmethod
    def _config_value(name: str, default: Any = None) -> Any:
        if has_app_context():
            return current_app.config.get(name, default)
        return default

    @staticmethod
    def _mock_mode_error() -> Optional[Dict[str, Any]]:
        environment = str(PaymentService._config_value("APP_ENV", "production")).lower()
        provider = str(PaymentService._config_value("PAYMENT_PROVIDER", "none")).lower()
        if environment not in NON_PRODUCTION_ENVS:
            return {
                "success": False,
                "erro": "A simulação de pagamento está desativada fora de desenvolvimento/testes.",
                "status_code": 403,
            }
        if provider != "mock":
            return {
                "success": False,
                "erro": "Defina PAYMENT_PROVIDER=mock apenas no ambiente local/de testes para usar esta simulação.",
                "status_code": 409,
            }
        return None

    @staticmethod
    def _pedido_do_cliente(pedido_id: int, account_id: int, account_type: str):
        if account_type != "PERSONAL":
            return None, {
                "success": False,
                "erro": "Somente o cliente pode iniciar ou simular o pagamento deste pedido.",
                "status_code": 403,
            }
        pedido = db.session.get(Pedido, pedido_id)
        if not pedido:
            return None, {
                "success": False,
                "erro": "Pedido não encontrado.",
                "status_code": 404,
            }
        if pedido.user_id != account_id:
            return None, {
                "success": False,
                "erro": "Você não tem acesso ao pagamento deste pedido.",
                "status_code": 403,
            }
        return pedido, None

    @staticmethod
    def criar_pagamento(
        pedido_id: int,
        account_id: int,
        account_type: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        # The create/query contract is provider-neutral. Apply the special
        # environment gate only when someone explicitly selects the mock; real
        # adapters can use this same endpoint once implemented and configured.
        selected_provider = str(
            PaymentService._config_value("PAYMENT_PROVIDER", "none")
        ).strip().lower()
        if selected_provider == "mock":
            mode_error = PaymentService._mock_mode_error()
            if mode_error:
                return mode_error

        pedido, error = PaymentService._pedido_do_cliente(
            pedido_id, account_id, account_type
        )
        if error:
            return error
        if pedido.status != "PENDENTE_PAGAMENTO":
            return {
                "success": False,
                "erro": "Só é possível iniciar pagamento de pedido pendente.",
                "status_code": 409,
            }

        existing = PaymentAttempt.query.filter_by(order_id=pedido_id).first()
        if existing:
            return {
                "success": True,
                "created": False,
                "mensagem": "A tentativa de pagamento já existe; nenhuma tentativa duplicada foi criada.",
                "dados": PaymentService._to_dict(existing),
            }

        key = str(idempotency_key or f"order:{pedido_id}:payment:v1").strip()
        if not key or len(key) > 200:
            return {
                "success": False,
                "erro": "Idempotency-Key deve conter de 1 a 200 caracteres.",
                "status_code": 400,
            }

        try:
            provider = get_payment_provider()
            method = PaymentMethod(pedido.payment_method)
            provider.validar_metodo(method)
            amount = Decimal(str(pedido.total)).quantize(Decimal("0.01"))
            command = CreatePaymentCommand(
                order_id=str(pedido.id),
                idempotency_key=key,
                amount=amount,
                method=method,
                currency="BRL",
                metadata={"order_code": pedido.order_code},
            )
            result = provider.create_payment(command)
            if result.amount != amount or result.currency != "BRL":
                db.session.rollback()
                return {
                    "success": False,
                    "erro": "O provedor retornou valor/moeda diferente do pedido.",
                    "status_code": 502,
                }
            if result.provider != provider.provider_name:
                db.session.rollback()
                return {
                    "success": False,
                    "erro": "A identificação do provedor retornado é inválida.",
                    "status_code": 502,
                }

            attempt = PaymentAttempt(
                order_id=pedido.id,
                provider=result.provider,
                provider_payment_id=result.provider_payment_id,
                idempotency_key=key,
                payment_method=method.value,
                status=result.status.value,
                amount=result.amount,
                currency=result.currency,
                approval_url=result.approval_url,
                pix_copy_paste=result.pix_copy_paste,
                pix_qr_code_base64=result.pix_qr_code_base64,
                boleto_url=result.boleto_url,
                boleto_line=result.boleto_line,
                message=result.message,
            )
            db.session.add(attempt)
            db.session.commit()
            return {
                "success": True,
                "created": True,
                "mensagem": "Tentativa de pagamento criada. O pagamento permanece pendente até um resultado válido.",
                "dados": PaymentService._to_dict(attempt),
            }
        except (ValueError, PaymentProviderError) as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 409}
        except IntegrityError:
            db.session.rollback()
            # Concurrent requests with the same order converge on the unique row.
            existing = PaymentAttempt.query.filter_by(order_id=pedido_id).first()
            if existing:
                return {
                    "success": True,
                    "created": False,
                    "mensagem": "A tentativa de pagamento já existe.",
                    "dados": PaymentService._to_dict(existing),
                }
            return {
                "success": False,
                "erro": "Conflito ao registrar a tentativa de pagamento; tente novamente.",
                "status_code": 409,
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao registrar tentativa de pagamento.",
                "status_code": 500,
            }

    @staticmethod
    def consultar_pagamento(
        pedido_id: int, account_id: int, account_type: str
    ) -> Dict[str, Any]:
        pedido, error = PaymentService._pedido_do_cliente(
            pedido_id, account_id, account_type
        )
        if error:
            return error
        attempt = PaymentAttempt.query.filter_by(order_id=pedido_id).first()
        if not attempt:
            return {
                "success": False,
                "erro": "Este pedido ainda não possui uma tentativa de pagamento.",
                "status_code": 404,
            }
        return {
            "success": True,
            "mensagem": "Pagamento consultado.",
            "dados": PaymentService._to_dict(attempt),
        }

    @staticmethod
    def simular_resultado(
        pedido_id: int,
        account_id: int,
        account_type: str,
        outcome: str,
    ) -> Dict[str, Any]:
        mode_error = PaymentService._mock_mode_error()
        if mode_error:
            return mode_error

        pedido, error = PaymentService._pedido_do_cliente(
            pedido_id, account_id, account_type
        )
        if error:
            return error
        attempt = PaymentAttempt.query.filter_by(order_id=pedido_id).first()
        if not attempt:
            return {
                "success": False,
                "erro": "Crie a tentativa de pagamento antes de simular o resultado.",
                "status_code": 404,
            }
        if attempt.provider != "mock":
            return {
                "success": False,
                "erro": "Somente pagamentos do provedor mock aceitam resultado simulado.",
                "status_code": 409,
            }

        try:
            provider = get_payment_provider()
            simulator = getattr(provider, "simulate_outcome", None)
            if not callable(simulator):
                return {
                    "success": False,
                    "erro": "O provedor configurado não suporta simulação.",
                    "status_code": 409,
                }
            event = simulator(
                provider_payment_id=attempt.provider_payment_id,
                order_reference=str(pedido.id),
                amount=Decimal(str(pedido.total)).quantize(Decimal("0.01")),
                currency="BRL",
                outcome=outcome,
            )
        except (ValueError, PaymentProviderError) as exc:
            return {"success": False, "erro": str(exc), "status_code": 400}

        # Correlate every simulated event with the existing order and payment;
        # never accept amounts or payment IDs supplied by the HTTP caller.
        expected_amount = Decimal(str(pedido.total)).quantize(Decimal("0.01"))
        persisted_attempt_amount = Decimal(str(attempt.amount)).quantize(Decimal("0.01"))
        if (
            event.provider != attempt.provider
            or event.provider_payment_id != attempt.provider_payment_id
            or event.order_reference != str(pedido.id)
            or event.amount != expected_amount
            or event.amount != persisted_attempt_amount
            or event.currency != "BRL"
        ):
            return {
                "success": False,
                "erro": "O evento simulado não corresponde ao pedido/pagamento persistido.",
                "status_code": 409,
            }

        if attempt.last_event_id == event.event_id:
            return {
                "success": True,
                "mensagem": "Evento repetido ignorado; nenhuma alteração foi aplicada novamente.",
                "dados": PaymentService._to_dict(attempt),
            }

        if attempt.status == PaymentStatus.APPROVED.value:
            return {
                "success": True,
                "mensagem": "Este pagamento já foi aprovado; o estado não será rebaixado.",
                "dados": PaymentService._to_dict(attempt),
            }

        if attempt.status in {PaymentStatus.REJECTED.value, PaymentStatus.CANCELLED.value}:
            return {
                "success": False,
                "erro": (
                    "Esta tentativa já terminou como recusada/cancelada. "
                    "A política para criar uma nova tentativa ainda não está habilitada."
                ),
                "status_code": 409,
                "dados": PaymentService._to_dict(attempt),
            }

        if event.status is PaymentStatus.APPROVED:
            if pedido.status == "CANCELADO":
                attempt.status = PaymentStatus.ACTION_REQUIRED.value
                attempt.last_event_id = event.event_id
                attempt.message = (
                    "A aprovação simulada chegou após o cancelamento; requer análise manual."
                )
                db.session.commit()
                return {
                    "success": False,
                    "erro": attempt.message,
                    "status_code": 409,
                    "dados": PaymentService._to_dict(attempt),
                }

            # OrderService commits this same scoped session together with stock
            # changes. Thus the approved attempt, order transition and stock
            # decrement succeed in one transaction for the normal success path.
            attempt.status = PaymentStatus.APPROVED.value
            attempt.last_event_id = event.event_id
            attempt.message = "Resultado fictício aprovado; nenhuma cobrança real ocorreu."
            result = OrderService.confirmar_pagamento(pedido.id)
            if result.get("success"):
                db.session.commit()
                current_attempt = db.session.get(PaymentAttempt, attempt.id)
                return {
                    "success": True,
                    "mensagem": result.get("mensagem", "Pagamento simulado aprovado."),
                    "pedido": result.get("dados"),
                    "dados": PaymentService._to_dict(current_attempt),
                }

            # Stock/transition validation may roll back the session. Record the
            # simulated approval as requiring review instead of claiming the
            # order was paid or decrementing stock partially.
            db.session.rollback()
            current_attempt = db.session.get(PaymentAttempt, attempt.id)
            current_attempt.status = PaymentStatus.ACTION_REQUIRED.value
            current_attempt.last_event_id = event.event_id
            current_attempt.message = result.get(
                "erro", "Não foi possível concluir a confirmação simulada."
            )
            db.session.commit()
            return {
                "success": False,
                "erro": current_attempt.message,
                "status_code": result.get("status_code", 409),
                "dados": PaymentService._to_dict(current_attempt),
            }

        if pedido.status != "PENDENTE_PAGAMENTO":
            return {
                "success": False,
                "erro": "O pedido não está pendente; o resultado não pode alterar seu estado.",
                "status_code": 409,
            }

        attempt.status = event.status.value
        attempt.last_event_id = event.event_id
        attempt.message = {
            PaymentStatus.REJECTED: "Pagamento fictício recusado; o pedido continua pendente.",
            PaymentStatus.PENDING: "Pagamento fictício continua pendente.",
            PaymentStatus.CANCELLED: "Tentativa de pagamento fictícia cancelada.",
        }.get(event.status, "Estado do pagamento simulado atualizado.")
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao registrar resultado do pagamento simulado.",
                "status_code": 500,
            }
        return {
            "success": True,
            "mensagem": attempt.message,
            "dados": PaymentService._to_dict(attempt),
        }

    @staticmethod
    def _to_dict(attempt: PaymentAttempt) -> Dict[str, Any]:
        return {
            "id": attempt.id,
            "order_id": attempt.order_id,
            "provider": attempt.provider,
            "provider_payment_id": attempt.provider_payment_id,
            "payment_method": attempt.payment_method,
            "status": attempt.status,
            "amount": float(attempt.amount),
            "currency": attempt.currency,
            "approval_url": attempt.approval_url,
            "pix_copy_paste": attempt.pix_copy_paste,
            "pix_qr_code_base64": attempt.pix_qr_code_base64,
            "boleto_url": attempt.boleto_url,
            "boleto_line": attempt.boleto_line,
            "message": attempt.message,
            "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
            "updated_at": attempt.updated_at.isoformat() if attempt.updated_at else None,
        }
