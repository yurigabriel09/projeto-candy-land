import os
import requests
from urllib.parse import urlencode
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


class FacebookAuthService:

    AUTH_URL = "https://www.facebook.com/dialog/oauth"
    GRAPH_URL = "https://graph.facebook.com"

    @staticmethod
    def gerar_url_autorizacao():
        client_id = os.getenv("FACEBOOK_CLIENT_ID")
        redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI")

        if not client_id:
            raise ValueError("FACEBOOK_CLIENT_ID não configurado.")

        if not redirect_uri:
            raise ValueError("FACEBOOK_REDIRECT_URI não configurado.")

        parametros = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "email,public_profile",
            "response_type": "code",
        }

        return f"{FacebookAuthService.AUTH_URL}?{urlencode(parametros)}"

    @staticmethod
    def _serializer():
        secret_key = os.getenv("SECRET_KEY")

        if not secret_key:
            raise ValueError("SECRET_KEY não configurado.")

        return URLSafeTimedSerializer(secret_key, salt="facebook-auth")

    @staticmethod
    def processar_callback(code):
        if not code:
            raise ValueError("Código do Facebook não informado.")

        client_id = os.getenv("FACEBOOK_CLIENT_ID")
        client_secret = os.getenv("FACEBOOK_CLIENT_SECRET")
        redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI")

        if not client_id:
            raise ValueError("FACEBOOK_CLIENT_ID não configurado.")

        if not client_secret:
            raise ValueError("FACEBOOK_CLIENT_SECRET não configurado.")

        if not redirect_uri:
            raise ValueError("FACEBOOK_REDIRECT_URI não configurado.")

        resposta_token = requests.get(
            f"{FacebookAuthService.GRAPH_URL}/oauth/access_token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=10,
        )

        if not resposta_token.ok:
            raise ValueError("Não foi possível obter o token do Facebook.")

        dados_token = resposta_token.json()
        access_token = dados_token.get("access_token")

        if not access_token:
            raise ValueError("O Facebook não retornou um token de acesso.")

        resposta_usuario = requests.get(
            f"{FacebookAuthService.GRAPH_URL}/me",
            params={"fields": "id,name,email", "access_token": access_token},
            timeout=10,
        )

        if not resposta_usuario.ok:
            raise ValueError("Não foi possível obter os dados da conta Facebook.")

        dados_usuario = resposta_usuario.json()

        facebook_id = dados_usuario.get("id")
        nome = dados_usuario.get("name")
        email = dados_usuario.get("email")

        if not facebook_id:
            raise ValueError("O Facebook não retornou o identificador da conta.")

        if email:
            email = email.strip().lower()

        ticket = FacebookAuthService._serializer().dumps(
            {"id": facebook_id, "nome": nome, "email": email}
        )

        return ticket

    @staticmethod
    def validar_ticket(ticket):
        if not ticket:
            raise ValueError("Ticket do Facebook não informado.")

        try:
            return FacebookAuthService._serializer().loads(ticket, max_age=300)

        except SignatureExpired:
            raise ValueError("A autenticação do Facebook expirou. Tente novamente.")

        except BadSignature:
            raise ValueError("Ticket de autenticação do Facebook inválido.")