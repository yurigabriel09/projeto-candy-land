import re
import secrets
from datetime import UTC, datetime, timedelta

from app.config.config import telefone_compartilhado_permitido
from app.database.database import db
from app.models.auth_attempt import TentativaAutenticacao
from app.models.auth_code import CodigoAutenticacao
from app.models.restaurant import Restaurante
from app.models.user import Usuario
from app.services.account_identity_service import telefone_esta_em_uso
from app.services.email_service import EmailService
from app.services.google_auth_service import GoogleAuthService
from app.services.token_service import TokenService
from app.services.whatsapp_service import WhatsAppService
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash


class AuthService:
    @staticmethod
    def _buscar_conta_por_canal(canal, valor):
        """Localiza uma conta pelo único identificador escolhido no aplicativo."""
        if canal == "EMAIL":
            email = (valor or "").strip().lower()
            usuarios = Usuario.query.filter(
                db.func.lower(Usuario.email) == email
            ).all()
            restaurantes = Restaurante.query.filter(
                db.func.lower(Restaurante.email) == email
            ).all()
        elif canal == "WHATSAPP":
            telefone = AuthService._normalizar_telefone(valor)
            usuarios = [
                usuario for usuario in Usuario.query.all()
                if AuthService._normalizar_telefone(usuario.telefone) == telefone
            ]
            restaurantes = [
                restaurante for restaurante in Restaurante.query.all()
                if AuthService._normalizar_telefone(restaurante.telefone) == telefone
            ]
        else:
            return None, None, {
                "success": False,
                "erro": "Canal de autenticação inválido.",
                "status_code": 400,
            }

        contas = [("PERSONAL", item) for item in usuarios]
        contas.extend(("BUSINESS", item) for item in restaurantes)

        if len(contas) > 1:
            return None, None, {
                "success": False,
                "erro": (
                    "Este contato está vinculado a mais de uma conta. "
                    "Entre usando o e-mail para identificar a conta correta."
                ),
                "status_code": 409,
            }

        if not contas:
            return None, None, None

        tipo_conta, conta = contas[0]
        if tipo_conta == "PERSONAL" and getattr(conta, "status", "ACTIVE") != "ACTIVE":
            return None, None, {
                "success": False,
                "erro": "Usuário inativo.",
                "status_code": 403,
            }
        if tipo_conta == "BUSINESS" and not conta.ativo:
            return None, None, {
                "success": False,
                "erro": "Restaurante inativo.",
                "status_code": 403,
            }
        return tipo_conta, conta, None

    @staticmethod
    def _resposta_sessao_conta_existente(tipo_conta, conta):
        """Cria o JWT para uma conta existente validada pelo provedor social."""
        if tipo_conta == "PERSONAL":
            if getattr(conta, "status", "ACTIVE") != "ACTIVE":
                return {
                    "success": False,
                    "erro": "Usuário inativo.",
                    "status_code": 403,
                }
            nome = conta.nome_completo
            campo_nome = "nome_completo"
        else:
            if not conta.ativo:
                return {
                    "success": False,
                    "erro": "Restaurante inativo.",
                    "status_code": 403,
                }
            nome = conta.nome
            campo_nome = "nome"

        email = (conta.email or "").strip().lower()
        dados = {
            "tipo_conta": tipo_conta,
            "id": conta.id,
            "email": email,
            "telefone": conta.telefone,
            "novo_cadastro": False,
            "token": TokenService.gerar_token(tipo_conta, conta.id, email),
        }
        dados[campo_nome] = nome
        return {
            "success": True,
            "mensagem": "Autenticação concluída com sucesso.",
            "dados": dados,
        }

    @staticmethod
    def iniciar_autenticacao(canal, valor):
        try:
            canal = (canal or "").strip().upper()
            valor = (valor or "").strip()

            if canal not in ("EMAIL", "WHATSAPP"):
                return {
                    "success": False,
                    "erro": "Canal de autenticação inválido.",
                    "status_code": 400,
                }

            if canal == "EMAIL":
                valor = valor.lower()
                if not AuthService._email_valido(valor):
                    return {
                        "success": False,
                        "erro": "E-mail inválido.",
                        "status_code": 400,
                    }
            else:
                valor = AuthService._normalizar_telefone(valor)
                if not valor:
                    return {
                        "success": False,
                        "erro": "Celular inválido.",
                        "status_code": 400,
                    }

            _, conta, conflito = AuthService._buscar_conta_por_canal(
                canal, valor
            )
            if conflito:
                return conflito

            if conta is not None:
                email = (conta.email or "").strip().lower()
                telefone = AuthService._normalizar_telefone(conta.telefone)
                if not email or not telefone:
                    return {
                        "success": False,
                        "erro": (
                            "A conta encontrada não possui e-mail e celular "
                            "válidos cadastrados."
                        ),
                        "status_code": 409,
                    }
            else:
                email = valor if canal == "EMAIL" else None
                telefone = valor if canal == "WHATSAPP" else None

            tentativa = TentativaAutenticacao(
                canal_inicial=canal,
                email=email,
                telefone=telefone,
                expira_em=datetime.now(UTC).replace(tzinfo=None)
                + timedelta(minutes=15),
            )

            db.session.add(tentativa)
            db.session.flush()

            resultado = AuthService._gerar_e_enviar_codigo(tentativa, canal, valor)
            if not resultado["success"]:
                db.session.rollback()
                return resultado

            db.session.commit()
            return {
                "success": True,
                "mensagem": resultado["mensagem"],
                "tentativa_id": tentativa.id,
                "proximo_canal": "WHATSAPP" if canal == "EMAIL" else "EMAIL",
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao iniciar autenticação.",
                "status_code": 500,
            }

    @staticmethod
    def solicitar_segundo_codigo(tentativa_id, valor):
        try:
            tentativa = db.session.get(TentativaAutenticacao, tentativa_id)
            if not tentativa:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação não encontrada.",
                    "status_code": 404,
                }
            if tentativa.concluida:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação já concluída.",
                    "status_code": 400,
                }

            agora = datetime.now(UTC).replace(tzinfo=None)
            if agora > tentativa.expira_em:
                tentativa.concluida = True
                db.session.commit()
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação expirada.",
                    "status_code": 401,
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
                    "status_code": 401,
                }

            segundo_canal = (
                "WHATSAPP" if tentativa.canal_inicial == "EMAIL" else "EMAIL"
            )
            valor = (valor or "").strip()
            if segundo_canal == "EMAIL":
                valor = valor.lower()
                if not AuthService._email_valido(valor):
                    return {
                        "success": False,
                        "erro": "E-mail inválido.",
                        "status_code": 400,
                    }
                tentativa.email = valor
            else:
                valor = AuthService._normalizar_telefone(valor)
                if not valor:
                    return {
                        "success": False,
                        "erro": "Celular inválido.",
                        "status_code": 400,
                    }
                tentativa.telefone = valor

            resultado = AuthService._gerar_e_enviar_codigo(
                tentativa, segundo_canal, valor
            )
            if not resultado["success"]:
                db.session.rollback()
                return resultado

            db.session.commit()
            return {
                "success": True,
                "mensagem": resultado["mensagem"],
                "tentativa_id": tentativa.id,
                "canal": segundo_canal,
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao solicitar segundo código.",
                "status_code": 500,
            }

    @staticmethod
    def verificar_codigo(tentativa_id, codigo, tipo_conta=None):
        try:
            tentativa = db.session.get(TentativaAutenticacao, tentativa_id)
            if not tentativa:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação não encontrada.",
                    "status_code": 404,
                }
            if tentativa.concluida:
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação já concluída.",
                    "status_code": 400,
                }

            agora = datetime.now(UTC).replace(tzinfo=None)
            if agora > tentativa.expira_em:
                tentativa.concluida = True
                db.session.commit()
                return {
                    "success": False,
                    "erro": "Tentativa de autenticação expirada.",
                    "status_code": 401,
                }

            registro = (
                CodigoAutenticacao.query.filter_by(
                    tentativa_id=tentativa.id, usado=False
                )
                .order_by(CodigoAutenticacao.id.desc())
                .first()
            )
            if not registro:
                return {
                    "success": False,
                    "erro": "Código inválido.",
                    "status_code": 401,
                }
            if agora > registro.expira_em:
                registro.usado = True
                db.session.commit()
                return {
                    "success": False,
                    "erro": "Código expirado.",
                    "status_code": 401,
                }
            if not check_password_hash(registro.codigo_hash, codigo):
                return {
                    "success": False,
                    "erro": "Código inválido.",
                    "status_code": 401,
                }

            registro.usado = True
            if registro.tipo == "EMAIL":
                tentativa.email_validado = True
            elif registro.tipo == "WHATSAPP":
                tentativa.telefone_validado = True

            # Para uma conta existente, somente o canal selecionado precisa ser
            # validado. Para cadastro novo, falta o outro contato e o OTP continua.
            valor_inicial = (
                tentativa.email
                if tentativa.canal_inicial == "EMAIL"
                else tentativa.telefone
            )
            tipo_conta, conta, conflito = AuthService._buscar_conta_por_canal(
                tentativa.canal_inicial, valor_inicial
            )
            if conflito:
                tentativa.concluida = True
                db.session.commit()
                return conflito

            if conta is not None:
                tentativa.email = (conta.email or "").strip().lower()
                tentativa.telefone = AuthService._normalizar_telefone(conta.telefone)
                resultado = AuthService._finalizar_autenticacao(
                    tentativa, tipo_conta=tipo_conta
                )
                if not resultado["success"]:
                    db.session.rollback()
                    return resultado
                tentativa.concluida = True
                db.session.commit()
                return resultado

            if not tentativa.email_validado or not tentativa.telefone_validado:
                db.session.commit()
                return {
                    "success": True,
                    "mensagem": "Código validado com sucesso.",
                    "proximo_canal": (
                        "WHATSAPP" if registro.tipo == "EMAIL" else "EMAIL"
                    ),
                    "tentativa_id": tentativa.id,
                }

            resultado = AuthService._finalizar_autenticacao(tentativa, tipo_conta=tipo_conta)

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
                "status_code": 500,
            }

    @staticmethod
    def _finalizar_autenticacao(tentativa, tipo_conta=None):
        permitir_telefone_compartilhado = telefone_compartilhado_permitido(
            current_app.config
        )

        email_verificado = (tentativa.email or "").strip().lower()

        if permitir_telefone_compartilhado:
            usuarios = (
                {
                    u.id: u
                    for u in Usuario.query.filter(
                        db.func.lower(Usuario.email) == email_verificado
                    ).all()
                }
                if email_verificado
                else {}
            )
            restaurantes = (
                {
                    r.id: r
                    for r in Restaurante.query.filter(
                        db.func.lower(Restaurante.email) == email_verificado
                    ).all()
                }
                if email_verificado
                else {}
            )
        else:
            usuarios_email = (
                Usuario.query.filter(
                    db.func.lower(Usuario.email) == email_verificado
                ).all()
                if email_verificado
                else []
            )
            usuarios_telefone = Usuario.query.filter_by(
                telefone=tentativa.telefone
            ).all()
            restaurantes_email = (
                Restaurante.query.filter(
                    db.func.lower(Restaurante.email) == email_verificado
                ).all()
                if email_verificado
                else []
            )
            restaurantes_telefone = Restaurante.query.filter_by(
                telefone=tentativa.telefone
            ).all()

            usuarios = {u.id: u for u in usuarios_email + usuarios_telefone}
            restaurantes = {r.id: r for r in restaurantes_email + restaurantes_telefone}

        if len(usuarios) > 1 or len(restaurantes) > 1 or (usuarios and restaurantes):
            return {
                "success": False,
                "erro": "Os dados informados estão vinculados a contas diferentes.",
                "status_code": 409,
            }

        if tipo_conta is None:
            if usuarios:
                tipo_conta = "PERSONAL"
            elif restaurantes:
                tipo_conta = "BUSINESS"

        # 1. Se a requisição veio do portal de parceiros (BUSINESS), busca na tabela de restaurantes
        if tipo_conta == "BUSINESS" and restaurantes:
            restaurante = next(iter(restaurantes.values()))

            if not restaurante.ativo:
                return {
                    "success": False,
                    "erro": "Restaurante inativo.",
                    "status_code": 403,
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
                    "nome": restaurante.nome,
                    "email": restaurante.email,
                    "telefone": restaurante.telefone,
                    "novo_cadastro": False,
                    "token": TokenService.gerar_token(
                        "BUSINESS", restaurante.id, restaurante.email
                    ),
                },
            }

        # 2. Se a requisição veio da área do comprador (PERSONAL), busca na tabela de usuários
        if tipo_conta == "PERSONAL" and usuarios:
            usuario = next(iter(usuarios.values()))

            if getattr(usuario, "status", "ACTIVE") != "ACTIVE":
                return {
                    "success": False,
                    "erro": "Usuário inativo.",
                    "status_code": 403,
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
                    "nome_completo": usuario.nome_completo,
                    "email": usuario.email,
                    "telefone": usuario.telefone,
                    "novo_cadastro": False,
                    "token": TokenService.gerar_token(
                        "PERSONAL", usuario.id, usuario.email
                    ),
                },
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
                "tentativa_id": tentativa.id,
            },
        }

    @staticmethod
    def autenticar_google(credential, telefone=None):
        try:
            try:
                dados_google = GoogleAuthService.validar_credencial(credential)
            except ValueError as erro:
                mensagem = str(erro)
                status_code = 500 if "não configurado" in mensagem else 401
                return {
                    "success": False,
                    "erro": mensagem,
                    "status_code": status_code,
                }

            email = (dados_google.get("email") or "").strip().lower()
            if not email:
                return {
                    "success": False,
                    "erro": "O Google não retornou um e-mail válido.",
                    "status_code": 401,
                }

            usuarios = Usuario.query.filter(
                db.func.lower(Usuario.email) == email
            ).all()
            restaurantes = Restaurante.query.filter(
                db.func.lower(Restaurante.email) == email
            ).all()
            if (
                len(usuarios) > 1
                or len(restaurantes) > 1
                or (usuarios and restaurantes)
            ):
                return {
                    "success": False,
                    "erro": "O e-mail está vinculado a contas diferentes.",
                    "status_code": 409,
                }

            # O token Google comprova o e-mail. Para conta existente, login direto.
            if usuarios:
                return AuthService._resposta_sessao_conta_existente(
                    "PERSONAL", usuarios[0]
                )
            if restaurantes:
                return AuthService._resposta_sessao_conta_existente(
                    "BUSINESS", restaurantes[0]
                )

            if not telefone:
                return {
                    "success": False,
                    "erro": "Celular é necessário para concluir o cadastro.",
                    "status_code": 400,
                    "precisa_telefone": True,
                    "email": email,
                }

            telefone_normalizado = AuthService._normalizar_telefone(telefone)
            if not telefone_normalizado:
                return {
                    "success": False,
                    "erro": "Celular inválido.",
                    "status_code": 400,
                }
            if (
                not telefone_compartilhado_permitido(current_app.config)
                and telefone_esta_em_uso(telefone_normalizado)
            ):
                return {
                    "success": False,
                    "erro": "Este celular já está vinculado a outra conta.",
                    "status_code": 409,
                }

            tentativa = TentativaAutenticacao(
                canal_inicial="EMAIL",
                email=email,
                telefone=telefone_normalizado,
                email_validado=True,
                telefone_validado=False,
                expira_em=datetime.now(UTC).replace(tzinfo=None)
                + timedelta(minutes=15),
            )
            db.session.add(tentativa)
            db.session.flush()
            resultado = AuthService._gerar_e_enviar_codigo(
                tentativa, "WHATSAPP", telefone_normalizado
            )
            if not resultado["success"]:
                db.session.rollback()
                return resultado
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Código enviado para o WhatsApp.",
                "tentativa_id": tentativa.id,
                "proximo_canal": "WHATSAPP",
                "email": email,
                "telefone": telefone_normalizado,
                "novo_cadastro": True,
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao autenticar com o Google.",
                "status_code": 500,
            }

    @staticmethod
    def autenticar_facebook(dados_facebook, telefone=None):
        try:
            if not dados_facebook:
                return {
                    "success": False,
                    "erro": "Dados do Facebook não informados.",
                    "status_code": 400,
                }

            facebook_id = dados_facebook.get("id")
            if not facebook_id:
                return {
                    "success": False,
                    "erro": "Identificador do Facebook não informado.",
                    "status_code": 401,
                }

            email = (dados_facebook.get("email") or "").strip().lower()
            usuarios = []
            restaurantes = []
            if email:
                usuarios = Usuario.query.filter(
                    db.func.lower(Usuario.email) == email
                ).all()
                restaurantes = Restaurante.query.filter(
                    db.func.lower(Restaurante.email) == email
                ).all()

            if (
                len(usuarios) > 1
                or len(restaurantes) > 1
                or (usuarios and restaurantes)
            ):
                return {
                    "success": False,
                    "erro": "O e-mail está vinculado a contas diferentes.",
                    "status_code": 409,
                }

            # O Facebook já validou o e-mail; conta existente recebe sessão direta.
            if usuarios:
                return AuthService._resposta_sessao_conta_existente(
                    "PERSONAL", usuarios[0]
                )
            if restaurantes:
                return AuthService._resposta_sessao_conta_existente(
                    "BUSINESS", restaurantes[0]
                )

            if not telefone:
                return {
                    "success": False,
                    "erro": "Celular é necessário para concluir o cadastro.",
                    "status_code": 400,
                    "precisa_telefone": True,
                    "email": email or None,
                }

            telefone_normalizado = AuthService._normalizar_telefone(telefone)
            if not telefone_normalizado:
                return {
                    "success": False,
                    "erro": "Celular inválido.",
                    "status_code": 400,
                }
            if (
                not telefone_compartilhado_permitido(current_app.config)
                and telefone_esta_em_uso(telefone_normalizado)
            ):
                return {
                    "success": False,
                    "erro": "Este celular já está vinculado a outra conta.",
                    "status_code": 409,
                }

            tentativa = TentativaAutenticacao(
                canal_inicial="EMAIL",
                email=email or None,
                telefone=telefone_normalizado,
                email_validado=True,
                telefone_validado=False,
                expira_em=datetime.now(UTC).replace(tzinfo=None)
                + timedelta(minutes=15),
            )
            db.session.add(tentativa)
            db.session.flush()
            resultado = AuthService._gerar_e_enviar_codigo(
                tentativa, "WHATSAPP", telefone_normalizado
            )
            if not resultado["success"]:
                db.session.rollback()
                return resultado
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Código enviado para o WhatsApp.",
                "tentativa_id": tentativa.id,
                "proximo_canal": "WHATSAPP",
                "email": email or None,
                "telefone": telefone_normalizado,
                "novo_cadastro": True,
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao autenticar com o Facebook.",
                "status_code": 500,
            }

    @staticmethod
    def _gerar_e_enviar_codigo(tentativa, canal, destino):
        CodigoAutenticacao.query.filter_by(
            tentativa_id=tentativa.id, tipo=canal, usado=False
        ).update({"usado": True})

        codigo = str(secrets.randbelow(900000) + 100000)
        novo_codigo = CodigoAutenticacao(
            tentativa_id=tentativa.id,
            tipo=canal,
            destino=destino,
            codigo_hash=generate_password_hash(codigo),
            expira_em=datetime.now(UTC).replace(tzinfo=None)
            + timedelta(minutes=10),
            usado=False,
        )
        db.session.add(novo_codigo)

        try:
            if canal == "EMAIL":
                EmailService.enviar_codigo(destino, codigo)
                mensagem = "Código enviado para o e-mail informado."
            else:
                WhatsAppService.enviar_codigo(destino, codigo)
                mensagem = "Código enviado para o WhatsApp informado."
            return {"success": True, "mensagem": mensagem}
        except ValueError as erro:
            current_app.logger.warning("Falha ao enviar código de autenticação: %s", erro)
            return {
                "success": False,
                "erro": "Não foi possível enviar o código.",
                "status_code": 502,
            }

    @staticmethod
    def _email_valido(email):
        return bool(
            re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email)
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
