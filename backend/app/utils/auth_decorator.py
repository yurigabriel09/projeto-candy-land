from functools import wraps

import jwt
from flask import request, jsonify, make_response, g

from app.services.token_service import TokenService


def token_required(f):
    """
    Decorator para proteger rotas Flask.
    Exige header: Authorization: Bearer <token>

    Em caso de sucesso, injeta em flask.g:
      g.current_account_id   -> id do usuario/restaurante autenticado
      g.current_account_type -> "PERSONAL" ou "BUSINESS"
      g.current_account_email
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return make_response(
                jsonify({"erro": "Token de autenticação ausente."}),
                401
            )

        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = TokenService.verificar_token(token)
        except jwt.ExpiredSignatureError:
            return make_response(
                jsonify({"erro": "Sessão expirada. Faça login novamente."}),
                401
            )
        except jwt.PyJWTError:
            return make_response(
                jsonify({"erro": "Token inválido."}),
                401
            )

        g.current_account_id = payload.get("sub")
        g.current_account_type = payload.get("tipo_conta")
        g.current_account_email = payload.get("email")

        return f(*args, **kwargs)

    return decorated
