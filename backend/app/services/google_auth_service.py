import os

from app.config.config import Config
from google.auth.transport import requests
from google.oauth2 import id_token


class GoogleAuthService:
    @staticmethod
    def validar_credencial(credential):
        if not credential:
            raise ValueError("Credencial do Google não informada.")

        client_id = os.getenv("GOOGLE_CLIENT_ID")

        if not client_id:
            raise ValueError("GOOGLE_CLIENT_ID não configurado.")

        try:
            dados = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                client_id,
                clock_skew_in_seconds=Config.GOOGLE_CLOCK_SKEW_SECONDS,
            )
        except ValueError as erro:
            # Não registrar a credencial nem claims do token. Claims não assinados
            # não são confiáveis e podem conter dados pessoais.
            raise ValueError("Credencial do Google inválida.") from erro

        if not dados.get("email"):
            raise ValueError("O Google não retornou um e-mail válido.")

        if not dados.get("email_verified"):
            raise ValueError("O e-mail do Google não foi verificado.")

        return {
            "email": dados["email"].strip().lower(),
            "nome": dados.get("name"),
            "google_id": dados.get("sub"),
        }
