import os
import secrets
from datetime import datetime, timedelta

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

from app.database.database import db
from app.models.user import Usuario
from app.models.restaurant import Restaurante
from app.models.auth_code import CodigoAutenticacao
from app.services.email_service import EmailService

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
TWILIO_CONTENT_SID_VERIFICATION = os.getenv("TWILIO_CONTENT_SID_VERIFICATION")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


class AuthService:

    @staticmethod
    def _buscar_conta(destino, tipo):
        campo = "email" if tipo == "EMAIL" else "telefone"
        usuario = Usuario.query.filter_by(**{campo: destino}).first()
        restaurante = Restaurante.query.filter_by(**{campo: destino}).first()
        return usuario, restaurante


    @staticmethod
    def solicitar_codigo(destino, tipo="EMAIL"):
        try:
            usuario, restaurante = AuthService._buscar_conta(destino, tipo)

            if usuario and restaurante:
                return {"success": False, "erro": "Mais de uma conta encontrada.", "status_code": 409}

            conta = usuario or restaurante

            if not conta:
                return {"success": False, "erro": "Conta não encontrada.", "status_code": 404}

            if usuario and usuario.status != "ACTIVE":
                return {"success": False, "erro": "Usuário inativo.", "status_code": 403}

            if restaurante and not restaurante.ativo:
                return {"success": False, "erro": "Restaurante inativo.", "status_code": 403}

            CodigoAutenticacao.query.filter_by(
                destino=destino, tipo=tipo, usado=False
            ).update({"usado": True})

            codigo = str(secrets.randbelow(900000) + 100000)

            novo_codigo = CodigoAutenticacao(
                usuario_id=usuario.id if usuario else None,
                restaurante_id=restaurante.id if restaurante else None,
                tipo=tipo,
                destino=destino,
                codigo_hash=generate_password_hash(codigo),
                expira_em=datetime.utcnow() + timedelta(minutes=10),
                usado=False
            )

            db.session.add(novo_codigo)
            db.session.commit()

            if tipo == "EMAIL":
                try:
                    EmailService.enviar_codigo(destino, codigo)
                except ValueError:
                    db.session.delete(novo_codigo)
                    db.session.commit()
                    return {"success": False, "erro": "Não foi possível enviar o código por e-mail.", "status_code": 502}

            elif tipo == "WHATSAPP":
                try:
                    twilio_client.messages.create(
                        from_=TWILIO_WHATSAPP_NUMBER,
                        content_sid=TWILIO_CONTENT_SID_VERIFICATION,
                        content_variables=f'{{"1":"{codigo}"}}',
                        to=f"whatsapp:{destino}"
                    )
                except TwilioRestException as e:
                    db.session.delete(novo_codigo)
                    db.session.commit()
                    return {"success": False, "erro": f"Falha ao enviar código: {e.msg}", "status_code": 502}

            return {"success": True, "mensagem": f"Código enviado por {tipo.lower()}."}

        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao solicitar código de autenticação.", "status_code": 500}


    @staticmethod
    def verificar_codigo(destino, codigo, tipo="EMAIL"):
        try:
            registro = CodigoAutenticacao.query.filter_by(
                destino=destino, tipo=tipo, usado=False
            ).order_by(CodigoAutenticacao.id.desc()).first()

            if not registro:
                return {"success": False, "erro": "Código inválido.", "status_code": 401}

            if datetime.utcnow() > registro.expira_em:
                registro.usado = True
                db.session.commit()
                return {"success": False, "erro": "Código expirado.", "status_code": 401}

            if not check_password_hash(registro.codigo_hash, codigo):
                return {"success": False, "erro": "Código inválido.", "status_code": 401}

            registro.usado = True
            db.session.commit()

            tipo_conta = "PERSONAL" if registro.usuario_id else "BUSINESS"
            id_conta = registro.usuario_id or registro.restaurante_id

            return {
                "success": True,
                "mensagem": "Código validado com sucesso.",
                "dados": {"tipo_conta": tipo_conta, "id": id_conta, "destino": destino}
            }

        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao validar código.", "status_code": 500}