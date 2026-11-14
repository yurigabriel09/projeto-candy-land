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
            # Não registrar destinatário, código ou credenciais.
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
