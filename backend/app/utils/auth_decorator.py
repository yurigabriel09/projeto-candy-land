from functools import wraps

import jwt
from flask import g, jsonify, make_response, request

from app.services.token_service import TokenService

TIPOS_CONTA_VALIDOS = {"PERSONAL", "BUSINESS"}


def _erro_autorizacao(mensagem, status_code):
    return make_response(jsonify({"erro": mensagem}), status_code)


def token_required(f):
    """Exige um JWT válido e injeta os dados verificados em ``flask.g``."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        esquema, separador, token = auth_header.partition(" ")
        if esquema.lower() != "bearer" or not separador or not token.strip():
            return _erro_autorizacao("Token de autenticação ausente.", 401)

        try:
            payload = TokenService.verificar_token(token.strip())
        except jwt.ExpiredSignatureError:
            return _erro_autorizacao(
                "Sessão expirada. Faça login novamente.", 401
            )
        except jwt.PyJWTError:
            return _erro_autorizacao("Token inválido.", 401)

        if not isinstance(payload, dict):
            return _erro_autorizacao("Token inválido.", 401)

        raw_account_id = payload.get("sub")
        if isinstance(raw_account_id, bool) or not isinstance(raw_account_id, (str, int)):
            return _erro_autorizacao("Token inválido.", 401)
        try:
            account_id = int(raw_account_id)
        except (TypeError, ValueError):
            return _erro_autorizacao("Token inválido.", 401)

        account_type = payload.get("tipo_conta")
        email = payload.get("email")
        if (
            account_id <= 0
            or not isinstance(account_type, str)
            or account_type not in TIPOS_CONTA_VALIDOS
            or (email is not None and not isinstance(email, str))
        ):
            return _erro_autorizacao("Token inválido.", 401)

        g.current_account_id = account_id
        g.current_account_type = account_type
        g.current_account_email = email
        return f(*args, **kwargs)

    return decorated


def account_type_required(expected_type):
    """Autoriza somente o tipo de conta esperado (aplicar após ``token_required``)."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if getattr(g, "current_account_type", None) != expected_type:
                return _erro_autorizacao("Acesso não autorizado para esta conta.", 403)
            return f(*args, **kwargs)

        return decorated

    return decorator


def account_owner_required(expected_type, resource_id_parameter):
    """Restringe uma rota ao titular do recurso indicado pelo parâmetro da URL."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if getattr(g, "current_account_type", None) != expected_type:
                return _erro_autorizacao("Acesso não autorizado para esta conta.", 403)

            try:
                resource_id = int(kwargs.get(resource_id_parameter))
            except (TypeError, ValueError):
                return _erro_autorizacao("Acesso não autorizado para este recurso.", 403)

            if g.current_account_id != resource_id:
                return _erro_autorizacao("Acesso não autorizado para este recurso.", 403)
            return f(*args, **kwargs)

        return decorated

    return decorator
