import base64
import os

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
                f"Seu pagamento foi confirmado. Segue em anexo o comprovante do pedido "
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

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        if not response.ok:
            print("BREVO STATUS:", response.status_code)
            print("BREVO RESPONSE:", response.text)
            raise ValueError("Falha ao enviar comprovante pelo Brevo.")