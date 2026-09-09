import os
import random
from datetime import datetime, timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlalchemy.exc import SQLAlchemyError
from app.database.database import db
from app.models.user import Usuario

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
TWILIO_CONTENT_SID_VERIFICATION = os.getenv("TWILIO_CONTENT_SID_VERIFICATION")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


class AuthService:

    @staticmethod
    def _gerar_codigo():
        return str(random.randint(100000, 999999))


    @staticmethod
    def enviar_codigo_whatsapp(telefone):
        try:
            usuario = Usuario.query.filter_by(telefone=telefone).first()

            if not usuario:
                usuario = Usuario(telefone=telefone, ativo=False)
                db.session.add(usuario)

            codigo = AuthService._gerar_codigo()
            usuario.codigo_verificacao = codigo
            usuario.codigo_expira_em = datetime.utcnow() + timedelta(minutes=10)

            db.session.commit()

            client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                content_sid=TWILIO_CONTENT_SID_VERIFICATION,
                content_variables=f'{{"1":"{codigo}"}}',
                to=f"whatsapp:{telefone}"
            )

            return {"success": True, "mensagem": "Código enviado por WhatsApp!"}

        except TwilioRestException as e:
            db.session.rollback()
            return {"success": False, "erro": f"Falha ao enviar código: {e.msg}", "status_code": 400}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao salvar código no banco de dados.", "status_code": 500}


    @staticmethod
    def verificar_codigo_whatsapp(telefone, codigo):
        try:
            usuario = Usuario.query.filter_by(telefone=telefone).first()

            if not usuario:
                return {"success": False, "erro": "Nenhuma solicitação de código encontrada para esse telefone.", "status_code": 404}

            if usuario.codigo_verificacao != codigo:
                return {"success": False, "erro": "Código inválido.", "status_code": 400}

            if usuario.codigo_expira_em < datetime.utcnow():
                return {"success": False, "erro": "Código expirado. Solicite um novo.", "status_code": 400}

            criado = not usuario.ativo  # se já não estava ativo, essa é a primeira ativação

            usuario.ativo = True
            usuario.codigo_verificacao = None
            usuario.codigo_expira_em = None

            db.session.commit()

            mensagem = "Usuário verificado e ativado com sucesso!" if criado else "Login realizado com sucesso!"

            return {"success": True, "mensagem": mensagem, "dados": usuario.to_dict(), "criado": criado}

        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao verificar código.", "status_code": 500}