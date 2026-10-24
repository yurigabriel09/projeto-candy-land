from datetime import date

from app.config.config import telefone_compartilhado_permitido
from app.database.database import db
from app.models.address import Endereco
from app.models.auth_attempt import TentativaAutenticacao
from app.models.restaurant import Restaurante
from app.models.user import Usuario
from app.services.account_identity_service import (
    email_esta_em_uso,
    telefone_esta_em_uso,
)
from app.services.token_service import TokenService
from app.utils.formatter import normalizar_telefone
from flask import current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class UserService:
    @staticmethod
    def listar_usuarios():
        try:
            usuarios = Usuario.query.all()
            if not usuarios:
                return {
                    "success": True,
                    "mensagem": "Nenhum usuário cadastrado!",
                    "dados": [],
                }
            return {
                "success": True,
                "mensagem": "Lista de usuários cadastrados:",
                "dados": [usuario.to_dict() for usuario in usuarios],
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao consultar o banco de dados.",
                "status_code": 500,
            }

    @staticmethod
    def buscar_usuario(user_id):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {
                    "success": False,
                    "erro": "Usuário não encontrado.",
                    "status_code": 404,
                }
            return {
                "success": True,
                "mensagem": "Usuário encontrado:",
                "dados": usuario.to_dict(),
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao consultar o banco de dados.",
                "status_code": 500,
            }

    @staticmethod
    def criar_usuario(
        nome_completo,
        email,
        telefone,
        cpf,
        tentativa_id,
        data_nascimento=None,
        endereco=None,
    ):
        try:
            if not tentativa_id:
                return {
                    "success": False,
                    "erro": "Verificação de segurança (tentativa_id) é obrigatória.",
                    "status_code": 400,
                }

            tentativa = db.session.get(TentativaAutenticacao, tentativa_id)

            if not tentativa:
                return {
                    "success": False,
                    "erro": "Verificação de segurança não encontrada.",
                    "status_code": 404,
                }

            if (
                not tentativa.concluida
                or not tentativa.email_validado
                or not tentativa.telefone_validado
            ):
                return {
                    "success": False,
                    "erro": "Verificação por e-mail e WhatsApp ainda não foi concluída.",
                    "status_code": 401,
                }

            # Usa os dados verificados na tentativa como fonte de verdade.
            email = (tentativa.email or email or "").strip().lower()
            telefone = tentativa.telefone or telefone

            if not email:
                return {
                    "success": False,
                    "erro": "E-mail verificado é obrigatório para criar a conta.",
                    "status_code": 400,
                }

            # O e-mail deve identificar no máximo uma conta em toda a plataforma,
            # não apenas dentro da tabela de clientes.
            if email_esta_em_uso(email):
                return {
                    "success": False,
                    "erro": "E-mail já cadastrado em outra conta.",
                    "status_code": 409,
                }

            telefone_normalizado = normalizar_telefone(telefone)
            if (
                not telefone_compartilhado_permitido(current_app.config)
                and telefone_esta_em_uso(telefone_normalizado)
            ):
                return {
                    "success": False,
                    "erro": "Telefone já cadastrado.",
                    "status_code": 409,
                }

            if data_nascimento:
                data_nascimento = date.fromisoformat(data_nascimento)

            novo_usuario = Usuario(
                nome_completo=nome_completo,
                email=email,
                telefone=normalizar_telefone(telefone),
                cpf=cpf,
                data_nascimento=data_nascimento,
            )

            db.session.add(novo_usuario)
            db.session.flush()

            novo_endereco = Endereco(
                id_usuario=novo_usuario.id,
                cep=endereco.get("cep"),
                rua=endereco.get("rua"),
                numero=endereco.get("numero"),
                complemento=endereco.get("complemento"),
                bairro=endereco.get("bairro"),
                cidade=endereco.get("cidade"),
                estado=endereco.get("estado"),
                referencia=endereco.get("referencia"),
                latitude=endereco.get("latitude"),
                longitude=endereco.get("longitude"),
                tipo_endereco="RESIDENCIAL",
                principal=True,
                ativo=True,
            )

            db.session.add(novo_endereco)
            db.session.commit()

            return {
                "success": True,
                "mensagem": "Usuário e endereço criados com sucesso!",
                "dados": {
                    "usuario": novo_usuario.to_dict(),
                    "endereco": novo_endereco.to_dict(),
                    "token": TokenService.gerar_token(
                        "PERSONAL", novo_usuario.id, novo_usuario.email
                    ),
                },
            }

        except ValueError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Data de nascimento inválida.",
                "status_code": 400,
            }

        except IntegrityError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "E-mail, telefone ou CPF já cadastrado.",
                "status_code": 409,
            }

        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao criar usuário e endereço.",
                "status_code": 500,
            }

    @staticmethod
    def atualizar_usuario(
        user_id, nome_completo=None, email=None, telefone=None, data_nascimento=None
    ):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {
                    "success": False,
                    "erro": "Usuário não encontrado.",
                    "status_code": 404,
                }
            if nome_completo is not None:
                usuario.nome_completo = nome_completo
            if email is not None:
                email_normalizado = email.strip().lower()
                if email_esta_em_uso(
                    email_normalizado, usuario_id_ignorar=usuario.id
                ):
                    return {
                        "success": False,
                        "erro": "E-mail já cadastrado em outra conta.",
                        "status_code": 409,
                    }
                usuario.email = email_normalizado
            if telefone is not None:
                telefone_normalizado = normalizar_telefone(telefone)
                if (
                    not telefone_compartilhado_permitido(current_app.config)
                    and telefone_esta_em_uso(
                        telefone_normalizado, usuario_id_ignorar=usuario.id
                    )
                ):
                    return {
                        "success": False,
                        "erro": "Telefone já cadastrado em outra conta.",
                        "status_code": 409,
                    }
                usuario.telefone = telefone_normalizado
            if data_nascimento is not None:
                data_nascimento = date.fromisoformat(data_nascimento)
                usuario.data_nascimento = data_nascimento
            db.session.commit()
            return {
                "success": True,
                "mensagem": "Usuário atualizado com sucesso!",
                "dados": usuario.to_dict(),
            }
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao atualizar usuário.",
                "status_code": 500,
            }

    @staticmethod
    def deletar_usuario(user_id):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {
                    "success": False,
                    "erro": "Usuário não encontrado.",
                    "status_code": 404,
                }
            db.session.delete(usuario)
            db.session.commit()
            return {"success": True, "mensagem": "Usuário removido com sucesso!"}
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao remover usuário.",
                "status_code": 500,
            }
