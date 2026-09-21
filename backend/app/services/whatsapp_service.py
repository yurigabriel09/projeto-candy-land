import json
import os

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


class WhatsAppService:
    @staticmethod
    def enviar_codigo(destino, codigo):
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        numero_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER")
        content_sid = os.getenv("TWILIO_WHATSAPP_CONTENT_SID")

        if not account_sid or not auth_token or not numero_whatsapp or not content_sid:
            raise ValueError("Configuração do Twilio não encontrada.")

        telefone = WhatsAppService._normalizar_telefone(destino)

        if not telefone:
            raise ValueError("Número de celular inválido.")

        try:
            client = Client(account_sid, auth_token)

            mensagem = client.messages.create(
                from_=numero_whatsapp,
                to=f"whatsapp:{telefone}",
                content_sid=content_sid,
                content_variables=json.dumps({
                    "1": codigo
                })
            )

            return mensagem.sid

        except TwilioRestException as erro:
            print("TWILIO STATUS:", erro.status)
            print("TWILIO RESPONSE:", erro.msg)
            raise ValueError("Falha ao enviar código pelo WhatsApp.")

    @staticmethod
    def _normalizar_telefone(telefone):
        if not telefone:
            return None

        numeros = "".join(filter(str.isdigit, telefone))

        if numeros.startswith("55") and len(numeros) in (12, 13):
            return f"+{numeros}"

        if len(numeros) in (10, 11):
            return f"+55{numeros}"

        return None