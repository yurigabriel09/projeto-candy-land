from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database.database import db
from app.models.category import Categoria

class CategoryService:
    @staticmethod
    def listar_categorias(restaurant_id):
        try:
            categorias = Categoria.query.filter_by(id_restaurante=restaurant_id).order_by(Categoria.ordem_exibicao).all()
            return {"success": True, "mensagem": "Categorias listadas com sucesso.", "dados": [c.to_dict() for c in categorias]}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar categorias.", "status_code": 500}

    @staticmethod
    def buscar_categoria(categoria_id, restaurant_id):
        try:
            categoria = Categoria.query.filter_by(id=categoria_id, id_restaurante=restaurant_id).first()
            if not categoria:
                return {"success": False, "erro": "Categoria não encontrada.", "status_code": 404}
            return {"success": True, "mensagem": "Categoria encontrada.", "dados": categoria.to_dict()}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar categoria.", "status_code": 500}

    @staticmethod
    def criar_categoria(restaurant_id, dados):
        try:
            nova_categoria = Categoria(
                id_restaurante=restaurant_id,
                id_categoria_pai=dados.get("categoria_pai_id"),
                nome=dados.get("nome"),
                descricao=dados.get("descricao"),
                url_icone=dados.get("url_icone"),
                url_capa=dados.get("url_capa"),
                ordem_exibicao=dados.get("ordem_exibicao", 0),
                ativa=dados.get("ativa", True)
            )
            db.session.add(nova_categoria)
            db.session.commit()
            return {"success": True, "mensagem": "Categoria criada com sucesso!", "dados": nova_categoria.to_dict()}
        except IntegrityError:
            db.session.rollback()
            return {"success": False, "erro": "Você já tem uma categoria com esse nome.", "status_code": 409}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao criar categoria.", "status_code": 500}

    @staticmethod
    def atualizar_categoria(categoria_id, restaurant_id, dados):
        try:
            categoria = Categoria.query.filter_by(id=categoria_id, id_restaurante=restaurant_id).first()
            if not categoria:
                return {"success": False, "erro": "Categoria não encontrada.", "status_code": 404}

            if "nome" in dados:
                categoria.nome = dados["nome"]
            if "descricao" in dados:
                categoria.descricao = dados["descricao"]
            if "url_icone" in dados:
                categoria.url_icone = dados["url_icone"]
            if "url_capa" in dados:
                categoria.url_capa = dados["url_capa"]
            if "ordem_exibicao" in dados:
                categoria.ordem_exibicao = dados["ordem_exibicao"]
            if "ativa" in dados:
                categoria.ativa = dados["ativa"]
            if "categoria_pai_id" in dados:
                categoria.id_categoria_pai = dados["categoria_pai_id"]

            db.session.commit()
            return {"success": True, "mensagem": "Categoria atualizada com sucesso!", "dados": categoria.to_dict()}
        except IntegrityError:
            db.session.rollback()
            return {"success": False, "erro": "Você já tem uma categoria com esse nome.", "status_code": 409}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao atualizar categoria.", "status_code": 500}

    @staticmethod
    def deletar_categoria(categoria_id, restaurant_id):
        try:
            categoria = Categoria.query.filter_by(id=categoria_id, id_restaurante=restaurant_id).first()
            if not categoria:
                return {"success": False, "erro": "Categoria não encontrada.", "status_code": 404}
            db.session.delete(categoria)
            db.session.commit()
            return {"success": True, "mensagem": "Categoria removida com sucesso!"}
        except IntegrityError:
            db.session.rollback()
            return {"success": False, "erro": "Não é possível remover: existem produtos cadastrados nessa categoria.", "status_code": 409}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao remover categoria.", "status_code": 500}