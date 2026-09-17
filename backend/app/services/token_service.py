from datetime import datetime, timedelta

import jwt
from flask import current_app


class TokenService:
    ALGORITHM = "HS256"

    @staticmethod
    def gerar_token(tipo_conta, id_conta, email=None):
        """
        Gera um JWT assinado para o usuario (PERSONAL) ou restaurante (BUSINESS)
        recem autenticado.
        """
        agora = datetime.utcnow()
        horas_expiracao = current_app.config.get("JWT_EXPIRATION_HOURS", 24)

        payload = {
            "sub": str(id_conta),
            "tipo_conta": tipo_conta,
            "email": email,
            "iat": agora,
            "exp": agora + timedelta(hours=horas_expiracao)
        }

        return jwt.encode(
            payload,
            current_app.config["SECRET_KEY"],
            algorithm=TokenService.ALGORITHM
        )

    @staticmethod
    def verificar_token(token):
        """
        Decodifica e valida um JWT.
        Lanca jwt.ExpiredSignatureError ou jwt.PyJWTError caso invalido.
        """
        return jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=[TokenService.ALGORITHM]
        )
