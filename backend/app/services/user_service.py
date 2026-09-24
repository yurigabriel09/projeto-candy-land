from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.utils.formatter import normalizar_telefone
from app.database.database import db
from app.models.user import Usuario
from app.models.restaurant import Restaurante
from app.models.address import Endereco
from app.models.auth_attempt import TentativaAutenticacao
from app.services.token_service import TokenService
from flask import current_app


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
            telefone_normalizado = normalizar_telefone(telefone)

            if not current_app.config.get("ALLOW_DUPLICATE_PHONE"):
                telefone_em_uso = (
                    Usuario.query.filter_by(telefone=telefone_normalizado).first()
                    or Restaurante.query.filter_by(telefone=telefone_normalizado).first()
                )
                if telefone_em_uso:
                    return {"success": False, "erro": "Telefone já cadastrado.", "status_code": 409}
                
            if not tentativa_id:
                return {
                    "success": False,
                    "erro": "Verificação de segurança (tentativa_id) é obrigatória.",
                    "status_code": 400,
                }

            tentativa = TentativaAutenticacao.query.get(tentativa_id)

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

            # usa os dados já validados na tentativa como fonte de verdade,
            # em vez de confiar cegamente no que o front-end mandou
            email = tentativa.email or email
            telefone = tentativa.telefone or telefone

            if data_nascimento:
                data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()

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
                usuario.email = email
            if telefone is not None:
                usuario.telefone = normalizar_telefone(telefone)
            if data_nascimento is not None:
                data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
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
