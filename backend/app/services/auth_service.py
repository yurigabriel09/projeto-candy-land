from datetime import datetime, timedelta
import re
import secrets

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

from app.database.database import db
from app.models.user import Usuario
from app.models.restaurant import Restaurante
from app.models.auth_code import CodigoAutenticacao
from app.models.auth_attempt import TentativaAutenticacao
from app.services.email_service import EmailService
from app.services.whatsapp_service import WhatsAppService


class AuthService:
    @staticmethod
    def iniciar_autenticacao(canal, valor):
        try:
            canal = canal.strip().upper()
            valor = valor.strip()

            if canal not in ("EMAIL", "WHATSAPP"):
                return {
                    "success": False,
                    "erro": "Canal de autenticação inválido.",
                    "status_code": 400
                }

            if canal == "EMAIL":
                valor = valor.lower()

                if not AuthService._email_valido(valor):
                    return {
                        "success": False,
                        "erro": "E-mail inválido.",
                        "status_code": 400
                    }
            else:
                valor = AuthService._normalizar_telefone(valor)

                if not valor:
                    return {
                        "success": False,
                        "erro": "Celular inválido.",
                        "status_code": 400
                    }

            tentativa = TentativaAutenticacao(
                canal_inicial=canal,
                email=valor if canal == "EMAIL" else None,
                telefone=valor if canal == "WHATSAPP" else None,
                expira_em=datetime.utcnow() + timedelta(minutes=15)
            )

            db.session.add(tentativa)
            db.session.flush()

            resultado = AuthService._gerar_e_enviar_codigo(
                tentativa,
                canal,
                valor
            )

            if not resultado["success"]:
                db.session.rollback()
                return resultado

            db.session.commit()

            return {
                "success": True,
                "mensagem": resultado["mensagem"],
                "tentativa_id": tentativa.id,
                "proximo_canal": (
                    "WHATSAPP" if canal == "EMAIL" else "EMAIL"
                )
            }

        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao iniciar autenticação.",
                "status_code": 500
            }

    @staticmethod
    def solicitar_segundo_codigo(tentativa_id, valor):
        try:
            tentativa = TentativaAutenticacao.query.get(tentativa_id)

            if not tentativa:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação não encontrada.",
                    "status_code": 404
                }

            if tentativa.concluida:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação já concluída.",
                    "status_code": 400
                }

            if datetime.utcnow() > tentativa.expira_em:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação expirada.",
                    "status_code": 401
                }

            primeiro_canal_validado = (
                tentativa.email_validado
                if tentativa.canal_inicial == "EMAIL"
                else tentativa.telefone_validado
            )

            if not primeiro_canal_validado:
                return {
                    "success": False,
                    "erro": "O primeiro código ainda não foi validado.",
                    "status_code": 401
                }

            segundo_canal = (
                "WHATSAPP"
                if tentativa.canal_inicial == "EMAIL"
                else "EMAIL"
            )

            valor = valor.strip()

            if segundo_canal == "EMAIL":
                valor = valor.lower()

                if not AuthService._email_valido(valor):
                    return {
                        "success": False,
                        "erro": "E-mail inválido.",
                        "status_code": 400
                    }

                tentativa.email = valor
            else:
                valor = AuthService._normalizar_telefone(valor)

                if not valor:
                    return {
                        "success": False,
                        "erro": "Celular inválido.",
                        "status_code": 400
                    }

                tentativa.telefone = valor

            resultado = AuthService._gerar_e_enviar_codigo(
                tentativa,
                segundo_canal,
                valor
            )

            if not resultado["success"]:
                db.session.rollback()
                return resultado

            db.session.commit()

            return {
                "success": True,
                "mensagem": resultado["mensagem"],
                "tentativa_id": tentativa.id,
                "canal": segundo_canal
            }

        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao solicitar segundo código.",
                "status_code": 500
            }

    @staticmethod
    def verificar_codigo(tentativa_id, codigo):
        try:
            tentativa = TentativaAutenticacao.query.get(tentativa_id)

            if not tentativa:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação não encontrada.",
                    "status_code": 404
                }

            if tentativa.concluida:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação já concluída.",
                    "status_code": 400
                }

            if datetime.utcnow() > tentativa.expira_em:
                tentativa.concluida = True
                db.session.commit()

                return {
                    "success": False,
                    "erro": "Tentativa de autenticação expirada.",
                    "status_code": 401
                }

            registro = CodigoAutenticacao.query.filter_by(
                tentativa_id=tentativa.id,
                usado=False
            ).order_by(CodigoAutenticacao.id.desc()).first()

            if not registro:
                return {
                    "success": False,
                    "erro": "Código inválido.",
                    "status_code": 401
                }

            if datetime.utcnow() > registro.expira_em:
                registro.usado = True
                db.session.commit()

                return {
                    "success": False,
                    "erro": "Código expirado.",
                    "status_code": 401
                }

            if not check_password_hash(registro.codigo_hash, codigo):
                return {
                    "success": False,
                    "erro": "Código inválido.",
                    "status_code": 401
                }

            registro.usado = True

            if registro.tipo == "EMAIL":
                tentativa.email_validado = True
            elif registro.tipo == "WHATSAPP":
                tentativa.telefone_validado = True

            if not tentativa.email_validado or not tentativa.telefone_validado:
                db.session.commit()

                return {
                    "success": True,
                    "mensagem": "Código validado com sucesso.",
                    "proximo_canal": (
                        "WHATSAPP"
                        if registro.tipo == "EMAIL"
                        else "EMAIL"
                    ),
                    "tentativa_id": tentativa.id
                }

            resultado = AuthService._finalizar_autenticacao(tentativa)

            if not resultado["success"]:
                db.session.rollback()
                return resultado

            tentativa.concluida = True
            db.session.commit()

            return resultado

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "success": False,
                "erro": "Falha ao validar código.",
                "status_code": 500
            }

    @staticmethod
    def _gerar_e_enviar_codigo(tentativa, canal, destino):
        CodigoAutenticacao.query.filter_by(
            tentativa_id=tentativa.id,
            tipo=canal,
            usado=False
        ).update({"usado": True})

        codigo = str(secrets.randbelow(900000) + 100000)

        novo_codigo = CodigoAutenticacao(
            tentativa_id=tentativa.id,
            tipo=canal,
            destino=destino,
            codigo_hash=generate_password_hash(codigo),
            expira_em=datetime.utcnow() + timedelta(minutes=10),
            usado=False
        )

        db.session.add(novo_codigo)

        try:
            if canal == "EMAIL":
                EmailService.enviar_codigo(destino, codigo)
                mensagem = "Código enviado para o e-mail informado."
            else:
                WhatsAppService.enviar_codigo(destino, codigo)
                mensagem = "Código enviado para o WhatsApp informado."

            return {
                "success": True,
                "mensagem": mensagem
            }

        except ValueError as erro:
            print("ERRO DE ENVIO:", erro)

            return {
                "success": False,
                "erro": "Não foi possível enviar o código.",
                "status_code": 502
            }

    @staticmethod
    def _finalizar_autenticacao(tentativa):
        usuarios_email = Usuario.query.filter_by(
            email=tentativa.email
        ).all()

        usuarios_telefone = Usuario.query.filter_by(
            telefone=tentativa.telefone
        ).all()

        restaurantes_email = Restaurante.query.filter_by(
            email=tentativa.email
        ).all()

        restaurantes_telefone = Restaurante.query.filter_by(
            telefone=tentativa.telefone
        ).all()

        usuarios = {
            usuario.id: usuario
            for usuario in usuarios_email + usuarios_telefone
        }

        restaurantes = {
            restaurante.id: restaurante
            for restaurante in restaurantes_email + restaurantes_telefone
        }

        if len(usuarios) > 1 or len(restaurantes) > 1:
            return {
                "success": False,
                "erro": "Os dados informados estão vinculados a contas diferentes.",
                "status_code": 409
            }

        if usuarios and restaurantes:
            return {
                "success": False,
                "erro": "Os dados informados estão vinculados a contas diferentes.",
                "status_code": 409
            }

        if usuarios:
            usuario = next(iter(usuarios.values()))

            if getattr(usuario, "status", "ACTIVE") != "ACTIVE":
                return {
                    "success": False,
                    "erro": "Usuário inativo.",
                    "status_code": 403
                }

            if not usuario.email:
                usuario.email = tentativa.email

            if not usuario.telefone:
                usuario.telefone = tentativa.telefone

            return {
                "success": True,
                "mensagem": "Autenticação concluída com sucesso.",
                "dados": {
                    "tipo_conta": "PERSONAL",
                    "id": usuario.id,
                    "email": usuario.email,
                    "telefone": usuario.telefone,
                    "novo_cadastro": False
                }
            }

        if restaurantes:
            restaurante = next(iter(restaurantes.values()))

            if not restaurante.ativo:
                return {
                    "success": False,
                    "erro": "Restaurante inativo.",
                    "status_code": 403
                }

            if not restaurante.email:
                restaurante.email = tentativa.email

            if not restaurante.telefone:
                restaurante.telefone = tentativa.telefone

            return {
                "success": True,
                "mensagem": "Autenticação concluída com sucesso.",
                "dados": {
                    "tipo_conta": "BUSINESS",
                    "id": restaurante.id,
                    "email": restaurante.email,
                    "telefone": restaurante.telefone,
                    "novo_cadastro": False
                }
            }

        return {
            "success": True,
            "mensagem": "Autenticação concluída. Cadastro necessário.",
            "dados": {
                "tipo_conta": None,
                "id": None,
                "email": tentativa.email,
                "telefone": tentativa.telefone,
                "novo_cadastro": True,
                "tentativa_id": tentativa.id
            }
        }

    @staticmethod
    def _email_valido(email):
        return bool(
            re.match(
                r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
                email
            )
        )

    @staticmethod
    def _normalizar_telefone(telefone):
        if not telefone:
            return None

        numeros = "".join(filter(str.isdigit, telefone))

        if numeros.startswith("55") and len(numeros) in (12, 13):
            return f"+{numeros}"

        if len(numeros) in (10, 11):
            return f"+55{numeros}"

        return None