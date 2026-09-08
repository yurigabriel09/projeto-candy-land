from sqlalchemy.exc import SQLAlchemyError
from app.database.database import db
from app.models.product import Produto


class ProductService:
    @staticmethod
    def listar_produtos():

        try:
            produtos = Produto.query.all()

            if not produtos:
                return {
                    "success": True,
                    "mensagem": "Nenhum produto cadastrado!",
                    "dados": []
                }

            return {
                "success": True,
                "mensagem": "Listando os produtos cadastrados.",
                "dados": [produto.to_dict() for produto in produtos]
            }

        except SQLAlchemyError as e:

            return {
                "success": False,
                "erro": f"Falha ao consultar banco de dados: {e}",
                "status_code": 500
            }


    @staticmethod
    def buscar_produto(produto_id):

        try:
            produto = Produto.query.filter_by(id=produto_id).first()

            if not produto:
                return {
                    "success": False,
                    "mensagem": "Nenhum produto encontrado com esse ID.",
                    "status_code": 404
                }

            return {
                "success": True,
                "mensagem": "Produto encontrado!",
                "dados": produto.to_dict()
            }

        except SQLAlchemyError as e:
            return {
                "success": False,
                "erro": f"Falha ao consultar o banco de dados: {e}",
                "status_code": 500
            }