"""Payment orchestration shared by the mock now and real adapters later."""
from decimal import Decimal
from typing import Any, Dict, Mapping, Optional
from urllib.parse import parse_qs, urlparse

from flask import current_app, has_app_context
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database.database import db
from app.models.order import Pedido
from app.models.payment_attempt import PaymentAttempt
from app.models.user import Usuario
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
    def _referencia_preferencia_da_url(pedido_id: int, approval_url: Optional[str]) -> Optional[str]:
        """Recover the Checkout Pro preference ID from its saved redirect URL."""
        if not approval_url:
            return None
        try:
            parsed = urlparse(str(approval_url))
            parts = [part for part in parsed.path.split("/") if part]
            for index, part in enumerate(parts):
                if part.lower() == "redirect" and index + 1 < len(parts):
                    preference_id = parts[index + 1].strip()
                    if preference_id:
                        return f"pref:{pedido_id}:{preference_id}"
            query = parse_qs(parsed.query)
            for key in ("preference-id", "preference_id", "pref_id"):
                values = query.get(key) or []
                if values and str(values[0]).strip():
                    return f"pref:{pedido_id}:{str(values[0]).strip()}"
        except (TypeError, ValueError):
            return None
        return None

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
            environment = str(PaymentService._config_value("APP_ENV", "production")).strip().lower()
            # Enquanto o projeto estava em mock, alguns pedidos locais podem ter
            # uma tentativa fictícia persistida. Depois de configurar Mercado Pago,
            # permite substituir apenas essa tentativa pendente não produtiva; nunca
            # troca uma tentativa real nem reabre pagamento concluído/recusado.
            mock_substituivel = (
                existing.provider == "mock"
                and selected_provider != "mock"
                and environment in NON_PRODUCTION_ENVS
                and existing.status in {PaymentStatus.PENDING.value, PaymentStatus.CREATED.value}
            ) or (
                existing.provider == "paypal"
                and existing.status == PaymentStatus.CANCELLED.value
                and existing.last_event_id == "cancelled-by-customer"
                and selected_provider != "mock"
            )
            if mock_substituivel:
                db.session.delete(existing)
                db.session.flush()
            else:
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
            selection = str(pedido.payment_method or "").strip().upper()
            if selected_provider == "mock":
                provider_name = "mock"
                method = PaymentMethod.PIX if selection == "PIX" else PaymentMethod.CREDIT_CARD
            elif selection == "PIX":
                provider_name, method = "mercadopago", PaymentMethod.PIX
            elif selection == "PAYPAL":
                provider_name, method = "paypal", PaymentMethod.CARD
            elif selection == "MERCADO_PAGO":
                provider_name, method = "mercadopago", PaymentMethod.CARD
            elif selection in {"CARTAO", "CARTAO_CREDITO"}:
                provider_name = selected_provider if selected_provider in {"paypal", "mercadopago"} else "mercadopago"
                method = PaymentMethod.CREDIT_CARD if selection == "CARTAO_CREDITO" else PaymentMethod.CARD
            else:
                return {"success": False, "erro": "Forma de pagamento não suportada.", "status_code": 400}
            provider = get_payment_provider(provider_name)
            provider.validar_metodo(method)
            amount = Decimal(str(pedido.total)).quantize(Decimal("0.01"))
            cliente = db.session.get(Usuario, pedido.user_id)
            command = CreatePaymentCommand(
                order_id=str(pedido.id),
                idempotency_key=key,
                amount=amount,
                method=method,
                currency="BRL",
                payer_email=cliente.email if cliente else None,
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
                payment_method=pedido.payment_method,
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
        except ValueError as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 400}
        except PaymentProviderError as exc:
            # Erro do gateway externo não é conflito de estado da API CandyLand.
            # 502 deixa explícito que o backend não conseguiu concluir a operação no provedor.
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 502}
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

        if (
            attempt.provider == "mercadopago"
            and attempt.status in {PaymentStatus.REJECTED.value, PaymentStatus.CANCELLED.value}
            and not str(attempt.provider_payment_id).startswith("pref:")
        ):
            referencia_preferencia = PaymentService._referencia_preferencia_da_url(
                pedido_id, attempt.approval_url
            )
            if referencia_preferencia:
                attempt.provider_payment_id = referencia_preferencia
                try:
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    attempt = PaymentAttempt.query.filter_by(order_id=pedido_id).first()

        # O retorno do Checkout Pro e o painel podem consultar o estado real sem
        # tratar query params do navegador como prova de pagamento. O webhook é
        # o caminho principal; esta consulta é o caminho de reconciliação.
        if (
            attempt.provider == "mercadopago"
            and (
                attempt.status not in {
                    PaymentStatus.APPROVED.value,
                    PaymentStatus.REFUNDED.value,
                    PaymentStatus.REJECTED.value,
                    PaymentStatus.CANCELLED.value,
                }
                # A preference reference lets us query the most recent payment
                # after the customer retries a previously rejected checkout.
                or str(attempt.provider_payment_id).startswith("pref:")
            )
        ):
            try:
                provider = get_payment_provider(attempt.provider)
                result = provider.get_payment(attempt.provider_payment_id)
                PaymentService._registrar_resultado_gateway(
                    pedido, attempt, result, event_id=None
                )
                attempt = db.session.get(PaymentAttempt, attempt.id)
            except (PaymentProviderError, ValueError):
                # Sem pagamento aprovado ainda ou API indisponível: retornar o
                # estado persistido, sem declarar sucesso nem apagar o pedido.
                db.session.rollback()
                attempt = PaymentAttempt.query.filter_by(order_id=pedido_id).first()

        return {
            "success": True,
            "mensagem": "Pagamento consultado.",
            "dados": PaymentService._to_dict(attempt),
        }

    @staticmethod
    def processar_webhook_mercado_pago(
        headers: Mapping[str, str], raw_body: bytes, query_data_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Valida assinatura, consulta pagamento na API e reconcilia o pedido."""
        try:
            provider = get_payment_provider("mercadopago")
            if provider.provider_name != "mercadopago":
                return {
                    "success": False,
                    "erro": "O provedor de pagamento configurado não é o Mercado Pago.",
                    "status_code": 409,
                }
            event = provider.verify_webhook(headers, raw_body, query_data_id)
        except PaymentProviderError as exc:
            message = str(exc)
            code = 503 if "não configurado" in message.lower() else 401
            if has_app_context():
                # Log only the reason; never log X-Signature or webhook secret.
                current_app.logger.warning("Webhook Mercado Pago recusado: %s", message)
            return {"success": False, "erro": message, "status_code": code}

        if query_data_id and str(query_data_id) != event.provider_payment_id:
            return {
                "success": False,
                "erro": "O identificador assinado no webhook não corresponde ao pagamento validado.",
                "status_code": 401,
            }
        try:
            order_id = int(event.order_reference)
        except (TypeError, ValueError):
            return {
                "success": False,
                "erro": "Referência externa de pedido inválida no pagamento.",
                "status_code": 400,
            }

        pedido = db.session.get(Pedido, order_id)
        if not pedido:
            return {
                "success": False,
                "erro": "Pedido referenciado no pagamento não encontrado.",
                "status_code": 404,
            }
        attempt = PaymentAttempt.query.filter_by(order_id=order_id).first()
        if not attempt or attempt.provider != "mercadopago":
            return {
                "success": False,
                "erro": "Não existe tentativa do Mercado Pago vinculada a este pedido.",
                "status_code": 404,
            }
        if attempt.last_event_id == event.event_id:
            return {
                "success": True,
                "mensagem": "Webhook repetido ignorado.",
                "dados": PaymentService._to_dict(attempt),
            }
        if not str(attempt.provider_payment_id).startswith("pref:") and (
            str(attempt.provider_payment_id) != str(event.provider_payment_id)
        ):
            # A preference may be retried after a rejected/cancelled transaction.
            # Only allow a different payment ID to replace a terminal transaction
            # when a new signed event says pending/approved and the CandyLand order
            # is still waiting for payment.
            referencia_preferencia = str(attempt.provider_payment_id).startswith("pref:")
            evento_novo = event.event_id != attempt.last_event_id
            nova_tentativa_apos_falha = (
                attempt.status in {PaymentStatus.REJECTED.value, PaymentStatus.CANCELLED.value}
                and event.status in {PaymentStatus.PENDING, PaymentStatus.APPROVED}
                and (evento_novo or (referencia_preferencia and event.status is PaymentStatus.APPROVED))
                and pedido.status == "PENDENTE_PAGAMENTO"
            )
            if not nova_tentativa_apos_falha:
                return {
                    "success": False,
                    "erro": "O pagamento não corresponde à preferência persistida para este pedido.",
                    "status_code": 409,
                }

        if event.amount != Decimal(str(pedido.total)).quantize(Decimal("0.01")):
            return {
                "success": False,
                "erro": "O valor informado pelo Mercado Pago difere do total persistido do pedido.",
                "status_code": 409,
            }
        if event.currency != "BRL":
            return {
                "success": False,
                "erro": "A moeda do pagamento não é BRL.",
                "status_code": 409,
            }

        return PaymentService._registrar_resultado_gateway(
            pedido, attempt, event, event_id=event.event_id
        )

    @staticmethod
    def _registrar_resultado_gateway(pedido, attempt, result, event_id=None):
        """Persiste estados consultados/assinados; aprovação também confirma estoque."""
        expected_amount = Decimal(str(pedido.total)).quantize(Decimal("0.01"))
        received_amount = Decimal(str(result.amount)).quantize(Decimal("0.01"))
        if (
            result.provider != attempt.provider
            or received_amount != expected_amount
            or result.currency != "BRL"
        ):
            return {
                "success": False,
                "erro": "O resultado retornado pelo gateway não corresponde ao pedido persistido.",
                "status_code": 409,
                "dados": PaymentService._to_dict(attempt),
            }

        status = result.status

        if status is PaymentStatus.REFUNDED:
            # O reembolso externo não deve ser confundido com um fluxo de
            # cancelamento da CandyLand: exige reconciliar pedido/estoque manualmente.
            if str(result.provider_payment_id).strip():
                attempt.provider_payment_id = str(result.provider_payment_id).strip()
            attempt.status = PaymentStatus.ACTION_REQUIRED.value
            attempt.last_event_id = event_id or attempt.last_event_id
            attempt.message = (
                "O Mercado Pago informou reembolso. Confira pedido e estoque antes de encerrar a análise."
            )
            db.session.commit()
            return {
                "success": True,
                "mensagem": attempt.message,
                "dados": PaymentService._to_dict(attempt),
            }

        if attempt.status == PaymentStatus.APPROVED.value:
            return {
                "success": True,
                "mensagem": "Pagamento já confirmado; nenhum estado foi rebaixado.",
                "dados": PaymentService._to_dict(attempt),
            }
        if attempt.status in {PaymentStatus.REJECTED.value, PaymentStatus.CANCELLED.value}:
            # Checkout Pro may reuse one preference for another attempt. A new,
            # signed event with a pending/approved state may represent that retry;
            # an unaffiliated refresh or repeated terminal event cannot reopen it.
            referencia_preferencia = str(attempt.provider_payment_id).startswith("pref:")
            evento_novo = event_id is not None and event_id != attempt.last_event_id
            nova_tentativa_valida = (
                pedido.status == "PENDENTE_PAGAMENTO"
                and (
                    (status is PaymentStatus.APPROVED and (evento_novo or referencia_preferencia))
                    or (status is PaymentStatus.PENDING and (evento_novo or referencia_preferencia))
                )
            )
            if not nova_tentativa_valida:
                return {
                    "success": True,
                    "mensagem": "A tentativa anterior terminou sem aprovação. O pedido continua pendente e pode ser pago novamente pelo checkout.",
                    "dados": PaymentService._to_dict(attempt),
                }

        if status not in {
            PaymentStatus.APPROVED,
            PaymentStatus.PENDING,
            PaymentStatus.REJECTED,
            PaymentStatus.CANCELLED,
            PaymentStatus.REFUNDED,
        }:
            return {
                "success": True,
                "mensagem": "O pagamento ainda está em processamento no Mercado Pago.",
                "dados": PaymentService._to_dict(attempt),
            }

        previous_provider_payment_id = attempt.provider_payment_id
        # Keep the preference reference while a payment is pending/rejected so
        # get_payment() can search for the latest attempt made through that same
        # Checkout Pro preference. Once approved, persist the actual payment ID.
        manter_referencia_preferencia = (
            str(attempt.provider_payment_id).startswith("pref:")
            and status is not PaymentStatus.APPROVED
            and status is not PaymentStatus.REFUNDED
        )
        if str(result.provider_payment_id).strip() and not manter_referencia_preferencia:
            attempt.provider_payment_id = str(result.provider_payment_id).strip()
        attempt.last_event_id = event_id or attempt.last_event_id
        attempt.message = str(getattr(result, "message", "") or f"Estado atualizado pelo Mercado Pago: {status.value}.")[:500]

        # Only the provider's verified/query response can determine whether a
        # generic card payment ended up as credit or debit. Never infer it from
        # the browser's return URL or from the option selected before checkout.
        if status is PaymentStatus.APPROVED and pedido.payment_method in {"CARTAO", "CARTAO_CREDITO"}:
            actual_payment_type = str(getattr(result, "payment_type_id", "") or "").lower()
            if actual_payment_type == "credit_card":
                attempt.payment_method = "CARTAO_CREDITO"
                pedido.payment_method = "CARTAO_CREDITO"
            elif actual_payment_type == "debit_card":
                attempt.payment_method = "CARTAO_DEBITO"
                pedido.payment_method = "CARTAO_DEBITO"

        if status is PaymentStatus.APPROVED:
            if pedido.status == "CANCELADO":
                attempt.status = PaymentStatus.ACTION_REQUIRED.value
                attempt.message = "O Mercado Pago aprovou um pedido já cancelado; é necessária análise manual."
                db.session.commit()
                return {
                    "success": False,
                    "erro": attempt.message,
                    "status_code": 409,
                    "dados": PaymentService._to_dict(attempt),
                }
            attempt.status = PaymentStatus.APPROVED.value
            result_order = OrderService.confirmar_pagamento(pedido.id)
            if result_order.get("success"):
                db.session.commit()
                attempt = db.session.get(PaymentAttempt, attempt.id)
                return {
                    "success": True,
                    "mensagem": "Pagamento confirmado pelo Mercado Pago; pedido e estoque atualizados.",
                    "pedido": result_order.get("dados"),
                    "dados": PaymentService._to_dict(attempt),
                }
            db.session.rollback()
            attempt = db.session.get(PaymentAttempt, attempt.id)
            attempt.provider_payment_id = str(result.provider_payment_id or previous_provider_payment_id)
            attempt.status = PaymentStatus.ACTION_REQUIRED.value
            attempt.last_event_id = event_id or attempt.last_event_id
            attempt.message = str(result_order.get("erro") or "Não foi possível confirmar o pedido; verificação manual necessária.")[:500]
            db.session.commit()
            return {
                "success": False,
                "erro": attempt.message,
                "status_code": result_order.get("status_code", 409),
                "dados": PaymentService._to_dict(attempt),
            }

        if pedido.status != "PENDENTE_PAGAMENTO" and status in {
            PaymentStatus.REJECTED, PaymentStatus.CANCELLED
        }:
            return {
                "success": False,
                "erro": "O pedido já avançou e o resultado do pagamento não pode alterar esse estado.",
                "status_code": 409,
            }
        attempt.status = status.value
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao persistir o resultado do Mercado Pago.",
                "status_code": 500,
            }
        return {
            "success": True,
            "mensagem": attempt.message,
            "dados": PaymentService._to_dict(attempt),
        }

    @staticmethod
    def cancelar_tentativa_paypal(pedido_id: int, account_id: int, account_type: str, paypal_order_id: str) -> Dict[str, Any]:
        pedido, error = PaymentService._pedido_do_cliente(pedido_id, account_id, account_type)
        if error:
            return error
        attempt = PaymentAttempt.query.filter_by(order_id=pedido_id).first()
        if not attempt or attempt.provider != "paypal":
            return {"success": False, "erro": "Não existe tentativa PayPal para este pedido.", "status_code": 404}
        if str(paypal_order_id or "").strip() != str(attempt.provider_payment_id):
            return {"success": False, "erro": "A ordem informada não corresponde à ordem PayPal persistida.", "status_code": 409}
        if attempt.status == PaymentStatus.APPROVED.value or pedido.status != "PENDENTE_PAGAMENTO":
            return {"success": False, "erro": "O pagamento já foi concluído ou o pedido não está pendente.", "status_code": 409}
        try:
            provider = get_payment_provider("paypal")
            estado = provider.get_payment(attempt.provider_payment_id)
            if estado.status is PaymentStatus.APPROVED:
                return {"success": False, "erro": "A ordem PayPal já foi capturada; não é possível marcá-la como cancelada.", "status_code": 409}
            attempt.status = PaymentStatus.CANCELLED.value
            attempt.last_event_id = "cancelled-by-customer"
            attempt.message = "Checkout PayPal cancelado pelo comprador; nenhuma captura foi solicitada."
            db.session.commit()
            return {"success": True, "mensagem": attempt.message, "dados": PaymentService._to_dict(attempt)}
        except PaymentProviderError as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 502}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao registrar cancelamento da tentativa PayPal.", "status_code": 500}

    @staticmethod
    def capturar_paypal(pedido_id: int, account_id: int, account_type: str, paypal_order_id: str) -> Dict[str, Any]:
        pedido, error = PaymentService._pedido_do_cliente(pedido_id, account_id, account_type)
        if error:
            return error
        attempt = PaymentAttempt.query.filter_by(order_id=pedido_id).first()
        if not attempt or attempt.provider != "paypal":
            return {"success": False, "erro": "Não existe tentativa PayPal para este pedido.", "status_code": 404}
        if not paypal_order_id or str(paypal_order_id).strip() != str(attempt.provider_payment_id):
            return {"success": False, "erro": "A ordem retornada pelo PayPal não corresponde à ordem persistida.", "status_code": 409}
        if attempt.status == PaymentStatus.APPROVED.value:
            return {"success": True, "mensagem": "Pagamento PayPal já capturado.", "pedido": OrderService._to_dict(pedido), "dados": PaymentService._to_dict(attempt)}
        if pedido.status != "PENDENTE_PAGAMENTO":
            return {"success": False, "erro": "O pedido não está pendente de pagamento.", "status_code": 409}
        try:
            provider = get_payment_provider("paypal")
            result = provider.capture_payment(attempt.provider_payment_id, f"{attempt.idempotency_key}:capture")
            return PaymentService._registrar_resultado_gateway(pedido, attempt, result, event_id=None)
        except PaymentProviderError as exc:
            db.session.rollback()
            return {"success": False, "erro": str(exc), "status_code": 502}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao registrar a captura PayPal.", "status_code": 500}

    @staticmethod
    def processar_webhook_paypal(headers: Mapping[str, str], raw_body: bytes) -> Dict[str, Any]:
        try:
            provider = get_payment_provider("paypal")
            event = provider.verify_webhook(headers, raw_body)
        except PaymentProviderError as exc:
            message = str(exc)
            code = 503 if "não configurado" in message.lower() else 401
            return {"success": False, "erro": message, "status_code": code}
        try:
            order_id = int(event.order_reference)
        except (TypeError, ValueError):
            return {"success": False, "erro": "Referência externa inválida no webhook PayPal.", "status_code": 400}
        pedido = db.session.get(Pedido, order_id)
        attempt = PaymentAttempt.query.filter_by(order_id=order_id).first()
        if not pedido or not attempt or attempt.provider != "paypal":
            return {"success": False, "erro": "Não existe tentativa PayPal vinculada ao pedido.", "status_code": 404}
        if attempt.last_event_id == event.event_id:
            return {"success": True, "mensagem": "Webhook PayPal repetido ignorado.", "dados": PaymentService._to_dict(attempt)}
        if str(attempt.provider_payment_id) != str(event.provider_payment_id):
            return {"success": False, "erro": "O webhook não corresponde à ordem PayPal persistida.", "status_code": 409}
        if event.amount != Decimal(str(pedido.total)).quantize(Decimal("0.01")) or event.currency != "BRL":
            return {"success": False, "erro": "O valor/moeda do webhook PayPal difere do pedido.", "status_code": 409}
        return PaymentService._registrar_resultado_gateway(pedido, attempt, event, event_id=event.event_id)

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
