from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database.database import db
from app.models.restaurant import Restaurante
from app.models.address import Endereco
from app.models.auth_attempt import TentativaAutenticacao
from app.services.token_service import TokenService
from flask import current_app
from app.models.user import Usuario

class RestauranteService:
    @staticmethod
    def listar_restaurantes():
        try:
            restaurantes = Restaurante.query.all()
            if not restaurantes:
                return {"success": True, "mensagem": "Nenhum restaurante cadastrado!", "dados": []}
            return {"success": True, "mensagem": "Lista de restaurantes cadastrados:", "dados": [restaurante.to_dict() for restaurante in restaurantes]}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def buscar_restaurante(restaurante_id):
        try:
            restaurante = Restaurante.query.get(restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            return {"success": True, "mensagem": "Restaurante encontrado:", "dados": restaurante.to_dict()}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def criar_restaurante(cnpj, razao_social, nome, email, telefone, cpf_responsavel,
                           tentativa_id, endereco, nome_responsavel=None, descricao=None,
                           valor_minimo_pedido=None, taxa_entrega_base=None,
                           raio_entrega_km=None, horario_funcionamento=None):
        try:
            telefone_normalizado = telefone

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
                    "status_code": 400
                }

            tentativa = TentativaAutenticacao.query.get(tentativa_id)

            if not tentativa:
                return {
                    "success": False,
                    "erro": "Verificação de segurança não encontrada.",
                    "status_code": 404
                }

            if not tentativa.concluida or not tentativa.email_validado or not tentativa.telefone_validado:
                return {
                    "success": False,
                    "erro": "Verificação por e-mail e WhatsApp ainda não foi concluída.",
                    "status_code": 401
                }

            email = tentativa.email or email
            telefone = tentativa.telefone or telefone

            novo_restaurante = Restaurante(
                cnpj=cnpj,
                razao_social=razao_social,
                nome=nome,
                nome_responsavel=nome_responsavel,
                email=email,
                telefone=telefone,
                cpf_responsavel=cpf_responsavel,
                descricao=descricao,
                valor_minimo_pedido=valor_minimo_pedido or 0,
                taxa_entrega_base=taxa_entrega_base or 0,
                raio_entrega_km=raio_entrega_km,
                horario_funcionamento=horario_funcionamento
            )

            db.session.add(novo_restaurante)
            db.session.flush()

            novo_endereco = Endereco(
                id_restaurante=novo_restaurante.id,
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
                tipo_endereco="COMERCIAL",
                principal=True,
                ativo=True
            )

            db.session.add(novo_endereco)
            db.session.flush()

            novo_restaurante.address_id = novo_endereco.id

            db.session.commit()

            return {
                "success": True,
                "mensagem": "Empresa e endereço criados com sucesso!",
                "dados": {
                    "restaurante": novo_restaurante.to_dict(),
                    "endereco": novo_endereco.to_dict(),
                    "token": TokenService.gerar_token(
                        "BUSINESS", novo_restaurante.id, novo_restaurante.email
                    )
                }
            }

        except IntegrityError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "CNPJ, e-mail ou telefone já cadastrado.",
                "status_code": 409
            }

        except SQLAlchemyError:
            db.session.rollback()
            return {
                "success": False,
                "erro": "Falha ao criar empresa e endereço.",
                "status_code": 500
            }

    @staticmethod
    def atualizar_restaurante(restaurante_id, nome=None, email=None):
        try:
            restaurante = Restaurante.query.get(restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            if nome is not None:
                restaurante.nome = nome
            if email is not None:
                restaurante.email = email
            db.session.commit()
            return {"success": True, "mensagem": "Restaurante atualizado com sucesso!", "dados": restaurante.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao atualizar restaurante.", "status_code": 500}

    @staticmethod
    def deletar_restaurante(restaurante_id):
        try:
            restaurante = Restaurante.query.get(restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            db.session.delete(restaurante)
            db.session.commit()
            return {"success": True, "mensagem": "Restaurante removido com sucesso!"}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao remover restaurante.", "status_code": 500}
    @staticmethod
    def listar_produtos_restaurante(restaurante_id):
        from app.models.product import Produto

        try:
            restaurante = db.session.get(Restaurante, restaurante_id)
            if not restaurante:
                return {"success": False, "erro": "Restaurante não encontrado.", "status_code": 404}
            produtos = Produto.query.filter_by(restaurant_id=restaurante_id).order_by(Produto.id).all()
            return {
                "success": True,
                "mensagem": "Produtos do restaurante:",
                "dados": [produto.to_dict() for produto in produtos]
            }
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}
