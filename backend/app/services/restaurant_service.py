from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database.database import db
from app.models.restaurant import Restaurante
from app.models.address import Endereco

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
    def criar_restaurante(cnpj, razao_social, nome, email, telefone, cpf_responsavel, endereco):
        try:
            novo_restaurante = Restaurante(
                cnpj=cnpj,
                razao_social=razao_social,
                nome=nome,
                email=email,
                telefone=telefone,
                cpf_responsavel=cpf_responsavel
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
                    "endereco": novo_endereco.to_dict()
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