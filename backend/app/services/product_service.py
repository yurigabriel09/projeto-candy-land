from sqlalchemy.exc import SQLAlchemyError
from app.database.database import db
from app.models.product import Produto
from app.models.category import Categoria

class ProductService:
    @staticmethod
    def _validar_categoria(category_id, restaurant_id):
        categoria = Categoria.query.filter_by(id=category_id).first()
        if not categoria:
            return {"success": False, "erro": "Categoria não encontrada.", "status_code": 404}
        if categoria.id_restaurante != restaurant_id:
            return {"success": False, "erro": "Essa categoria não pertence ao seu restaurante.", "status_code": 403}
        return {"success": True}

    @staticmethod
    def listar_produtos():
        try:
            produtos = Produto.query.all()
            if not produtos:
                return {"success": True, "mensagem": "Nenhum produto cadastrado!", "dados": []}
            return {"success": True, "mensagem": "Listando os produtos cadastrados.", "dados": [p.to_dict() for p in produtos]}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar banco de dados.", "status_code": 500}

    @staticmethod
    def buscar_produto(produto_id):
        try:
            produto = Produto.query.filter_by(id=produto_id).first()
            if not produto:
                return {"success": False, "erro": "Produto não encontrado.", "status_code": 404}
            return {"success": True, "mensagem": "Produto encontrado!", "dados": produto.to_dict()}
        except SQLAlchemyError:
            return {"success": False, "erro": "Falha ao consultar o banco de dados.", "status_code": 500}

    @staticmethod
    def criar_produto(restaurant_id, dados):
        try:
            category_id = dados.get("categoria_id")

            validacao = ProductService._validar_categoria(category_id, restaurant_id)
            if not validacao["success"]:
                return validacao

            novo_produto = Produto(
                restaurant_id=restaurant_id,
                category_id=category_id,
                name=dados.get("nome"),
                description=dados.get("descricao"),
                price=dados.get("preco"),
                is_available=dados.get("disponivel", True),
                is_imported=dados.get("importado", False),
                current_stock=dados.get("qtd_estoque", 0),
                allows_customization=dados.get("permite_customizacao", False),
                image_url=dados.get("imagem_url")
            )
            db.session.add(novo_produto)
            db.session.commit()
            return {"success": True, "mensagem": "Produto criado com sucesso!", "dados": novo_produto.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao criar produto.", "status_code": 500}

    @staticmethod
    def atualizar_produto(produto_id, restaurant_id, dados):
        try:
            produto = Produto.query.filter_by(id=produto_id).first()
            if not produto:
                return {"success": False, "erro": "Produto não encontrado.", "status_code": 404}

            if produto.restaurant_id != restaurant_id:
                return {"success": False, "erro": "Você não tem permissão para alterar este produto.", "status_code": 403}

            if "categoria_id" in dados:
                validacao = ProductService._validar_categoria(dados["categoria_id"], restaurant_id)
                if not validacao["success"]:
                    return validacao
                produto.category_id = dados["categoria_id"]

            if "nome" in dados:
                produto.name = dados["nome"]
            if "descricao" in dados:
                produto.description = dados["descricao"]
            if "preco" in dados:
                produto.price = dados["preco"]
            if "disponivel" in dados:
                produto.is_available = dados["disponivel"]
            if "importado" in dados:
                produto.is_imported = dados["importado"]
            if "qtd_estoque" in dados:
                produto.current_stock = dados["qtd_estoque"]
            if "permite_customizacao" in dados:
                produto.allows_customization = dados["permite_customizacao"]
            if "imagem_url" in dados:
                produto.image_url = dados["imagem_url"]

            db.session.commit()
            return {"success": True, "mensagem": "Produto atualizado com sucesso!", "dados": produto.to_dict()}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao atualizar produto.", "status_code": 500}

    @staticmethod
    def deletar_produto(produto_id, restaurant_id):
        try:
            produto = Produto.query.filter_by(id=produto_id).first()
            if not produto:
                return {"success": False, "erro": "Produto não encontrado.", "status_code": 404}

            if produto.restaurant_id != restaurant_id:
                return {"success": False, "erro": "Você não tem permissão para remover este produto.", "status_code": 403}

            db.session.delete(produto)
            db.session.commit()
            return {"success": True, "mensagem": "Produto removido com sucesso!"}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "erro": "Falha ao remover produto.", "status_code": 500}