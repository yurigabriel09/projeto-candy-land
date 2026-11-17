import base64
import logging
import os

import requests

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def enviar_codigo(destino, codigo):
        api_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL")
        sender_name = os.getenv("BREVO_SENDER_NAME", "CandyLand")

        if not api_key or not sender_email:
            raise ValueError(
                "O envio por e-mail não está configurado no backend (Brevo)."
            )

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": destino}],
            "subject": "Seu código de acesso - CandyLand",
            "textContent": (
                f"Seu código de acesso ao CandyLand é: {codigo}. "
                "Este código expira em 10 minutos."
            ),
        }

        try:
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": api_key,
                    "content-type": "application/json",
                },
                json=payload,
                timeout=(3.05, 10),
            )
        except requests.RequestException as erro:
            logger.warning(
                "Falha de rede ao chamar Brevo para envio de OTP (%s).",
                type(erro).__name__,
            )
            raise ValueError(
                "O serviço de e-mail está indisponível. Tente novamente."
            ) from erro

        if not response.ok:
            logger.warning(
                "Brevo recusou o envio de OTP (HTTP %s).",
                response.status_code,
            )
            raise ValueError(
                "O Brevo recusou o envio. Confira a chave de API e o remetente verificado."
            )

    @staticmethod
    def enviar_comprovante(destino, nome_cliente, codigo_pedido, pdf_bytes):
        """Envia o comprovante de compra em PDF como anexo (API do Brevo)."""
        api_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL")
        sender_name = os.getenv("BREVO_SENDER_NAME", "CandyLand")

        if not api_key or not sender_email:
            raise ValueError("Configuração do Brevo não encontrada.")

        primeiro_nome = (nome_cliente or "").strip().split(" ")[0] or "cliente"
        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": destino}],
            "subject": f"Seu comprovante de compra - Pedido {codigo_pedido}",
            "textContent": (
                f"Olá, {primeiro_nome}!\n\n"
                "Seu pagamento foi confirmado. Segue em anexo o comprovante do pedido "
                f"{codigo_pedido}.\n\n"
                "Este documento não tem valor fiscal.\n\n"
                "CandyLand - Doces de todos os mundos"
            ),
            "attachment": [
                {
                    "name": f"comprovante-{codigo_pedido}.pdf",
                    "content": base64.b64encode(pdf_bytes).decode("ascii"),
                }
            ],
        }

        try:
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": api_key,
                    "content-type": "application/json",
                },
                json=payload,
                timeout=(3.05, 15),
            )
        except requests.RequestException as erro:
            logger.warning(
                "Falha de rede ao chamar Brevo para envio de comprovante (%s).",
                type(erro).__name__,
            )
            raise ValueError(
                "O serviço de e-mail está indisponível. Tente novamente."
            ) from erro

        if not response.ok:
            logger.warning(
                "Brevo recusou o envio de comprovante (HTTP %s).",
                response.status_code,
            )
            raise ValueError("Falha ao enviar comprovante pelo Brevo.")
