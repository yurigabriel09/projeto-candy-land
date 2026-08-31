from sqlalchemy.exc import SQLAlchemyError
from app.database.database import db
from app.models.restaurantes import Restaurante

class RestauranteService:
    @staticmethod
    def listar_restaurantes():
        try:
            restaurantes = Restaurante.query.all()
            if not restaurantes:
                return {"success": True, "mensagem": "Nenhum restaurante cadastrado!", "dados": []}
            return {"success": True, "mensagem": "Lista de restaurantes cadastrados:", "dados": [u.to_dict() for u in restaurantes]}
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
    def criar_restaurante(nome, email):
        try:
            novo_restaurante = Restaurante(nome=nome, email=email)
            db.session.add(novo_restaurante)
            db.session.commit()
            return {"success": True, "mensagem": "Restaurante criado com sucesso!", "dados": novo_restaurante.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao criar restaurante.", "status_code": 500}

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