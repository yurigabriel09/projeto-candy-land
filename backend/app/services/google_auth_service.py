import os

import jwt
from google.auth.transport import requests
from google.oauth2 import id_token

from app.config.config import Config


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
            # Diagnóstico seguro: mostramos apenas claims públicos do ID token,
            # nunca a credencial completa. Isso permite identificar mismatch
            # de audience/issuer/expiração sem expor o token.
            try:
                claims = jwt.decode(
                    credential,
                    options={
                        "verify_signature": False,
                        "verify_aud": False,
                    },
                )
                print(
                    "[GoogleAuthService] diagnóstico:",
                    {
                        "aud": claims.get("aud"),
                        "azp": claims.get("azp"),
                        "iss": claims.get("iss"),
                        "exp": claims.get("exp"),
                        "email": claims.get("email"),
                    },
                )
            except Exception as diagnostico_erro:
                print(
                    "[GoogleAuthService] não foi possível ler claims do token:",
                    diagnostico_erro,
                )

            print(f"[GoogleAuthService] falha na validação: {erro}")
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