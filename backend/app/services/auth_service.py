import re
import secrets
from datetime import UTC, datetime, timedelta

from app.config.config import telefone_compartilhado_permitido
from app.database.database import db
from app.models.auth_attempt import TentativaAutenticacao
from app.models.auth_code import CodigoAutenticacao
from app.models.restaurant import Restaurante
from app.models.user import Usuario
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
        """Inicia o primeiro fator sem tentar escolher uma conta pelo contato isolado."""
        try:
            canal = (canal or "").strip().upper()
            valor = (valor or "").strip()
            if canal not in ("EMAIL", "WHATSAPP"):
                return {"success": False, "erro": "Canal de autenticação inválido.", "status_code": 400}

            if canal == "EMAIL":
                valor = valor.lower()
                if not AuthService._email_valido(valor):
                    return {"success": False, "erro": "E-mail inválido.", "status_code": 400}
                email, telefone = valor, None
            else:
                valor = AuthService._normalizar_telefone(valor)
                if not valor:
                    return {"success": False, "erro": "Celular inválido.", "status_code": 400}
                email, telefone = None, valor

            tentativa = TentativaAutenticacao(
                canal_inicial=canal,
                email=email,
                telefone=telefone,
                email_validado=False,
                telefone_validado=False,
                concluida=False,
                expira_em=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15),
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
            return {"success": False, "erro": "Falha ao iniciar autenticação.", "status_code": 500}

    @staticmethod
    def solicitar_segundo_codigo(tentativa_id, valor):
        try:
            tentativa = db.session.get(TentativaAutenticacao, tentativa_id)
            if not tentativa:
                return {"success": False, "erro": "Tentativa de autenticação não encontrada.", "status_code": 404}
            if tentativa.concluida:
                return {"success": False, "erro": "Tentativa de autenticação já concluída.", "status_code": 400}
            agora = datetime.now(UTC).replace(tzinfo=None)
            if agora > tentativa.expira_em:
                tentativa.concluida = True
                db.session.commit()
                return {"success": False, "erro": "Tentativa de autenticação expirada.", "status_code": 401}

            primeiro_validado = tentativa.email_validado if tentativa.canal_inicial == "EMAIL" else tentativa.telefone_validado
            if not primeiro_validado:
                return {"success": False, "erro": "O primeiro código ainda não foi validado.", "status_code": 401}

            segundo_canal = "WHATSAPP" if tentativa.canal_inicial == "EMAIL" else "EMAIL"
            segundo_ja_validado = tentativa.telefone_validado if segundo_canal == "WHATSAPP" else tentativa.email_validado
            if segundo_ja_validado:
                return {"success": False, "erro": "O segundo fator já foi confirmado.", "status_code": 409}

            valor = (valor or "").strip()
            if segundo_canal == "EMAIL":
                valor = valor.lower()
                if not AuthService._email_valido(valor):
                    return {"success": False, "erro": "E-mail inválido.", "status_code": 400}
                tentativa.email = valor
            else:
                valor = AuthService._normalizar_telefone(valor)
                if not valor:
                    return {"success": False, "erro": "Celular inválido.", "status_code": 400}
                tentativa.telefone = valor

            resultado = AuthService._gerar_e_enviar_codigo(tentativa, segundo_canal, valor)
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
            return {"success": False, "erro": "Falha ao solicitar segundo código.", "status_code": 500}

    @staticmethod
    def verificar_codigo(tentativa_id, codigo, tipo_conta=None):
        """Valida os dois fatores; só emite sessão após cruzar e-mail + celular."""
        try:
            tentativa = db.session.get(TentativaAutenticacao, tentativa_id)
            if not tentativa:
                return {"success": False, "erro": "Tentativa de autenticação não encontrada.", "status_code": 404}
            if tentativa.concluida:
                return {"success": False, "erro": "Tentativa de autenticação já concluída.", "status_code": 400}
            agora = datetime.now(UTC).replace(tzinfo=None)
            if agora > tentativa.expira_em:
                tentativa.concluida = True
                db.session.commit()
                return {"success": False, "erro": "Tentativa de autenticação expirada.", "status_code": 401}

            primeiro_canal = tentativa.canal_inicial
            primeiro_validado = tentativa.email_validado if primeiro_canal == "EMAIL" else tentativa.telefone_validado
            canal_esperado = primeiro_canal if not primeiro_validado else ("WHATSAPP" if primeiro_canal == "EMAIL" else "EMAIL")
            registro = (
                CodigoAutenticacao.query.filter_by(tentativa_id=tentativa.id, usado=False)
                .order_by(CodigoAutenticacao.id.desc()).first()
            )
            if not registro:
                return {"success": False, "erro": "Código inválido ou já utilizado.", "status_code": 401}
            if registro.tipo != canal_esperado:
                return {"success": False, "erro": "O código informado não corresponde à etapa atual da autenticação.", "status_code": 401}
            if agora > registro.expira_em:
                registro.usado = True
                db.session.commit()
                return {"success": False, "erro": "Código expirado.", "status_code": 401}
            if not check_password_hash(registro.codigo_hash, str(codigo or "")):
                return {"success": False, "erro": "Código inválido.", "status_code": 401}

            registro.usado = True
            if registro.tipo == "EMAIL":
                tentativa.email_validado = True
            elif registro.tipo == "WHATSAPP":
                tentativa.telefone_validado = True

            if not tentativa.email_validado or not tentativa.telefone_validado:
                db.session.commit()
                return {
                    "success": True,
                    "mensagem": "Primeiro fator confirmado. Agora confirme o outro contato.",
                    "proximo_canal": "WHATSAPP" if not tentativa.telefone_validado else "EMAIL",
                    "tentativa_id": tentativa.id,
                }

            resultado = AuthService._finalizar_autenticacao(tentativa)
            # Os dois OTPs foram consumidos. Tanto sucesso quanto conflito encerram
            # esta tentativa; para corrigir contatos divergentes, o cliente reinicia.
            tentativa.concluida = True
            db.session.commit()
            return resultado
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao validar código.", "status_code": 500}

    @staticmethod
    def _localizar_conta_email_telefone(email, telefone):
        email = (email or "").strip().lower()
        telefone = AuthService._normalizar_telefone(telefone)
        if not email or not telefone:
            return None, None, {"success": False, "erro": "É necessário confirmar e-mail e celular.", "status_code": 409}

        usuarios_email = Usuario.query.filter(db.func.lower(Usuario.email) == email).all()
        restaurantes_email = Restaurante.query.filter(db.func.lower(Restaurante.email) == email).all()
        usuarios_telefone = [u for u in Usuario.query.all() if AuthService._normalizar_telefone(u.telefone) == telefone]
        restaurantes_telefone = [r for r in Restaurante.query.all() if AuthService._normalizar_telefone(r.telefone) == telefone]
        contas_email = [("PERSONAL", u) for u in usuarios_email] + [("BUSINESS", r) for r in restaurantes_email]
        contas_dupla = [
            (tipo, conta) for tipo, conta in contas_email
            if AuthService._normalizar_telefone(conta.telefone) == telefone
        ]

        if len(contas_email) > 1 or len(contas_dupla) > 1:
            return None, None, {"success": False, "erro": "O e-mail está vinculado a mais de uma conta. Procure o suporte para corrigir a identidade cadastral.", "status_code": 409}
        if len(contas_dupla) == 1:
            tipo, conta = contas_dupla[0]
            if tipo == "PERSONAL" and getattr(conta, "status", "ACTIVE") != "ACTIVE":
                return None, None, {"success": False, "erro": "Usuário inativo.", "status_code": 403}
            if tipo == "BUSINESS" and not conta.ativo:
                return None, None, {"success": False, "erro": "Restaurante inativo.", "status_code": 403}
            return tipo, conta, None

        telefone_em_uso = bool(usuarios_telefone or restaurantes_telefone)
        if contas_email:
            return None, None, {"success": False, "erro": "O e-mail e o celular confirmados pertencem a contas diferentes ou não correspondem ao mesmo cadastro.", "status_code": 409}
        if telefone_em_uso and not telefone_compartilhado_permitido(current_app.config):
            return None, None, {"success": False, "erro": "Este celular já está vinculado a outra conta. Confirme o e-mail cadastrado nessa conta.", "status_code": 409}
        # Um telefone já utilizado não escolhe a conta: em desenvolvimento, o e-mail
        # confirmado permite cadastro adicional; em produção, a regra de unicidade bloqueia.
        return None, None, None

    @staticmethod
    def _finalizar_autenticacao(tentativa, tipo_conta=None):
        if not tentativa.email_validado or not tentativa.telefone_validado:
            return {"success": False, "erro": "Os dois fatores ainda não foram confirmados.", "status_code": 401}
        tipo, conta, conflito = AuthService._localizar_conta_email_telefone(
            tentativa.email, tentativa.telefone
        )
        if conflito:
            return conflito
        if tipo == "BUSINESS" and conta:
            return {
                "success": True,
                "mensagem": "Autenticação concluída com sucesso.",
                "dados": {
                    "tipo_conta": "BUSINESS", "id": conta.id, "nome": conta.nome,
                    "email": (conta.email or "").strip().lower(), "telefone": conta.telefone,
                    "novo_cadastro": False,
                    "token": TokenService.gerar_token("BUSINESS", conta.id, conta.email),
                },
            }
        if tipo == "PERSONAL" and conta:
            return {
                "success": True,
                "mensagem": "Autenticação concluída com sucesso.",
                "dados": {
                    "tipo_conta": "PERSONAL", "id": conta.id,
                    "nome_completo": conta.nome_completo,
                    "email": (conta.email or "").strip().lower(), "telefone": conta.telefone,
                    "novo_cadastro": False,
                    "token": TokenService.gerar_token("PERSONAL", conta.id, conta.email),
                },
            }
        return {
            "success": True,
            "mensagem": "Contatos confirmados. Cadastro necessário.",
            "dados": {
                "tipo_conta": None, "id": None,
                "email": (tentativa.email or "").strip().lower(),
                "telefone": AuthService._normalizar_telefone(tentativa.telefone),
                "novo_cadastro": True, "tentativa_id": tentativa.id,
            },
        }

    @staticmethod
    def autenticar_google(credential, telefone=None):
        try:
            try:
                dados_google = GoogleAuthService.validar_credencial(credential)
            except ValueError as erro:
                mensagem = str(erro)
                return {"success": False, "erro": mensagem, "status_code": 500 if "não configurado" in mensagem else 401}
            email = (dados_google.get("email") or "").strip().lower()
            if not email:
                return {"success": False, "erro": "O Google não retornou um e-mail válido.", "status_code": 401}
            if not telefone:
                return {"success": False, "precisa_telefone": True, "email": email, "erro": "O Google confirmou seu e-mail. Informe o celular para receber o segundo fator."}
            telefone_normalizado = AuthService._normalizar_telefone(telefone)
            if not telefone_normalizado:
                return {"success": False, "erro": "Celular inválido.", "status_code": 400}

            tentativa = TentativaAutenticacao(
                canal_inicial="EMAIL", email=email, telefone=telefone_normalizado,
                email_validado=True, telefone_validado=False, concluida=False,
                expira_em=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15),
            )
            db.session.add(tentativa)
            db.session.flush()
            envio = AuthService._gerar_e_enviar_codigo(tentativa, "WHATSAPP", telefone_normalizado)
            if not envio["success"]:
                db.session.rollback()
                return envio
            db.session.commit()
            return {"success": True, "mensagem": "Google confirmou o e-mail. Código enviado ao celular.", "tentativa_id": tentativa.id, "proximo_canal": "WHATSAPP", "email": email, "telefone": telefone_normalizado}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao iniciar autenticação com Google.", "status_code": 500}

    @staticmethod
    def autenticar_facebook(dados_facebook, telefone=None):
        try:
            if not dados_facebook or not dados_facebook.get("id"):
                return {"success": False, "erro": "Identidade do Facebook inválida.", "status_code": 401}
            email = (dados_facebook.get("email") or "").strip().lower()
            if not email or not AuthService._email_valido(email):
                return {"success": False, "erro": "O Facebook não forneceu um e-mail válido. Verifique a permissão de e-mail do aplicativo Meta.", "status_code": 401}
            if not telefone:
                return {"success": False, "precisa_telefone": True, "email": email, "erro": "O Facebook confirmou seu e-mail. Informe o celular para receber o segundo fator."}
            telefone_normalizado = AuthService._normalizar_telefone(telefone)
            if not telefone_normalizado:
                return {"success": False, "erro": "Celular inválido.", "status_code": 400}

            tentativa = TentativaAutenticacao(
                canal_inicial="EMAIL", email=email, telefone=telefone_normalizado,
                email_validado=True, telefone_validado=False, concluida=False,
                expira_em=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15),
            )
            db.session.add(tentativa)
            db.session.flush()
            envio = AuthService._gerar_e_enviar_codigo(tentativa, "WHATSAPP", telefone_normalizado)
            if not envio["success"]:
                db.session.rollback()
                return envio
            db.session.commit()
            return {"success": True, "mensagem": "Facebook confirmou o e-mail. Código enviado ao celular.", "tentativa_id": tentativa.id, "proximo_canal": "WHATSAPP", "email": email, "telefone": telefone_normalizado}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao iniciar autenticação com Facebook.", "status_code": 500}

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
