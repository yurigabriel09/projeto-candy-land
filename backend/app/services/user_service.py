from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.database.database import db
from app.models.user import Usuario

class UserService:
    @staticmethod
    def listar_usuarios():
        try:
            usuarios = Usuario.query.all()
            if not usuarios:
                return {"success": True, "mensagem": "Nenhum usuário cadastrado!", "dados": []}
            return {"success": True, "mensagem": "Lista de usuários cadastrados:", "dados": [usuario.to_dict() for usuario in usuarios]}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def buscar_usuario(user_id):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {"success": False, "erro": "Usuário não encontrado.", "status_code": 404}
            return {"success": True, "mensagem": "Usuário encontrado:", "dados": usuario.to_dict()}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def criar_usuario(nome_completo, email, telefone, data_nascimento=None):
        try:
            if data_nascimento:
                data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
            
            novo_usuario = Usuario(
                nome_completo=nome_completo,
                email=email,
                telefone=telefone,
                data_nascimento=data_nascimento
            )
            db.session.add(novo_usuario)
            db.session.commit()
            return {"success": True, "mensagem": "Usuário criado com sucesso!", "dados": novo_usuario.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao criar usuário.", "status_code": 500}

    @staticmethod
    def atualizar_usuario(user_id, nome_completo=None, email=None, telefone=None, data_nascimento=None):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {"success": False, "erro": "Usuário não encontrado.", "status_code": 404}
            if nome_completo is not None:
                usuario.nome_completo = nome_completo
            if email is not None:
                usuario.email = email
            if telefone is not None:
                usuario.telefone = telefone
            if data_nascimento is not None:
                data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
                usuario.data_nascimento = data_nascimento
            db.session.commit()
            return {"success": True, "mensagem": "Usuário atualizado com sucesso!", "dados": usuario.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao atualizar usuário.", "status_code": 500}

    @staticmethod
    def deletar_usuario(user_id):
        try:
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return {"success": False, "erro": "Usuário não encontrado.", "status_code": 404}
            db.session.delete(usuario)
            db.session.commit()
            return {"success": True, "mensagem": "Usuário removido com sucesso!"}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao remover usuário.", "status_code": 500}