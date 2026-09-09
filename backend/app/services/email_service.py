import os
from urllib import response
import requests


class EmailService:
    @staticmethod
    def enviar_codigo(destino, codigo):
        api_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL")
        sender_name = os.getenv("BREVO_SENDER_NAME", "CandyLand")

        if not api_key or not sender_email:
            raise ValueError("Configuração do Brevo não encontrada.")

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": destino}],
            "subject": "Seu código de acesso - CandyLand",
            "textContent": f"Seu código de acesso ao CandyLand é: {codigo}. Este código expira em 10 minutos.",
        }

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=10,
        )

        if not response.ok:
            print("BREVO STATUS:", response.status_code)
            print("BREVO RESPONSE:", response.text)
            raise ValueError("Falha ao enviar e-mail pelo Brevo.")
