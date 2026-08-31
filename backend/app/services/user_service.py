from sqlalchemy.exc import SQLAlchemyError
from app.database.database import db
from app.models.user import Usuario

class UserService:
    @staticmethod
    def listar_usuarios():
        try:
            users = Usuario.query.all()
            if not users:
                return {"success": True, "mensagem": "Nenhum usuário cadastrado!", "dados": []}
            return {"success": True, "mensagem": "Lista de usuários cadastrados:", "dados": [u.to_dict() for u in users]}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def buscar_usuario(user_id):
        try:
            user = Usuario.query.get(user_id)
            if not user:
                return {"success": False, "erro": "Usuário não encontrado.", "status_code": 404}
            return {"success": True, "mensagem": "Usuário encontrado:", "dados": user.to_dict()}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def criar_usuario(nome, email):
        try:
            novo_usuario = Usuario(nome=nome, email=email)
            db.session.add(novo_usuario)
            db.session.commit()
            return {"success": True, "mensagem": "Usuário criado com sucesso!", "dados": novo_usuario.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao criar usuário.", "status_code": 500}

    @staticmethod
    def atualizar_usuario(user_id, nome=None, email=None):
        try:
            user = Usuario.query.get(user_id)
            if not user:
                return {"success": False, "erro": "Usuário não encontrado.", "status_code": 404}
            if nome is not None:
                user.nome = nome
            if email is not None:
                user.email = email
            db.session.commit()
            return {"success": True, "mensagem": "Usuário atualizado com sucesso!", "dados": user.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao atualizar usuário.", "status_code": 500}

    @staticmethod
    def deletar_usuario(user_id):
        try:
            user = Usuario.query.get(user_id)
            if not user:
                return {"success": False, "erro": "Usuário não encontrado.", "status_code": 404}
            db.session.delete(user)
            db.session.commit()
            return {"success": True, "mensagem": "Usuário removido com sucesso!"}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao remover usuário.", "status_code": 500}