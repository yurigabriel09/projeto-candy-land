from app.database.database import db
from app.models.item_order import ItemPedido
from app.models.order import Pedido
from app.models.product import Produto
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

LIMITE_PADRAO = 6
LIMITE_MAXIMO = 20
# Pedidos que não chegaram a ser pagos não contam como "comprado junto".
STATUS_IGNORADOS = ("PENDENTE_PAGAMENTO", "CANCELADO")

PESO_COMPRADO_JUNTO = 100   # cada pedido que tem o item base E o candidato
PESO_MESMA_CATEGORIA = 10
# Mais vendidos entram só como desempate/complemento (quantidade vendida, limitada).
TETO_POPULARIDADE = 9


class RecommendationService:
    @staticmethod
    def _erro(mensagem, status_code):
        return {"success": False, "erro": mensagem, "status_code": status_code}

    @staticmethod
    def recomendar(product_ids, limite=LIMITE_PADRAO):
        """Recomenda produtos com base no carrinho ou em um item selecionado.

        Critérios (em ordem de peso):
          1. comprados junto: aparecem nos mesmos pedidos que os itens base;
          2. mesma categoria dos itens base;
          3. mais vendidos do restaurante (complemento/desempate).
        Só recomenda produtos do mesmo restaurante, disponíveis e com estoque.
        """
        try:
            ids = sorted({int(i) for i in product_ids})
        except (TypeError, ValueError):
            return RecommendationService._erro("Os ids de produto devem ser números inteiros.", 400)
        if not ids:
            return RecommendationService._erro("Informe ao menos um produto (produto_id).", 400)

        try:
            limite = int(limite)
        except (TypeError, ValueError):
            return RecommendationService._erro("O limite deve ser um número inteiro.", 400)
        if limite < 1:
            return RecommendationService._erro("O limite deve ser maior que zero.", 400)
        limite = min(limite, LIMITE_MAXIMO)

        try:
            base = Produto.query.filter(Produto.id.in_(ids)).all()
            if len(base) != len(ids):
                return RecommendationService._erro("Um ou mais produtos informados não foram encontrados.", 404)

            restaurantes = {p.restaurant_id for p in base}
            if len(restaurantes) > 1:
                return RecommendationService._erro("Os produtos informados são de restaurantes diferentes.", 400)
            restaurant_id = restaurantes.pop()
            categorias_base = {p.category_id for p in base}

            candidatos = Produto.query.filter(
                Produto.restaurant_id == restaurant_id,
                Produto.id.notin_(ids),
                Produto.is_available.is_(True),
                Produto.current_stock > 0,
            ).all()
            if not candidatos:
                return {"success": True, "mensagem": "Nenhuma recomendação disponível.",
                        "dados": {"base": ids, "restaurante_id": restaurant_id, "recomendacoes": []}}

            pedidos_com_base = db.session.query(ItemPedido.id_pedido).filter(ItemPedido.id_produto.in_(ids))

            juntos = dict(
                db.session.query(ItemPedido.id_produto, func.count(func.distinct(ItemPedido.id_pedido)))
                .join(Pedido, Pedido.id == ItemPedido.id_pedido)
                .filter(
                    ItemPedido.id_pedido.in_(pedidos_com_base),
                    ItemPedido.id_produto.notin_(ids),
                    Pedido.status.notin_(STATUS_IGNORADOS),
                )
                .group_by(ItemPedido.id_produto)
                .all()
            )

            vendidos = dict(
                db.session.query(ItemPedido.id_produto, func.sum(ItemPedido.quantidade))
                .join(Pedido, Pedido.id == ItemPedido.id_pedido)
                .filter(Pedido.restaurant_id == restaurant_id, Pedido.status.notin_(STATUS_IGNORADOS))
                .group_by(ItemPedido.id_produto)
                .all()
            )

            ranqueados = []
            for produto in candidatos:
                qtd_junto = int(juntos.get(produto.id, 0))
                mesma_categoria = produto.category_id in categorias_base
                popularidade = min(int(vendidos.get(produto.id, 0) or 0), TETO_POPULARIDADE)
                score = qtd_junto * PESO_COMPRADO_JUNTO + (PESO_MESMA_CATEGORIA if mesma_categoria else 0) + popularidade
                if qtd_junto:
                    motivo = "COMPRADO_JUNTO"
                elif mesma_categoria:
                    motivo = "MESMA_CATEGORIA"
                else:
                    motivo = "MAIS_PEDIDOS" if popularidade else "DESTAQUE"
                ranqueados.append((score, produto, motivo))

            # Mais pontos primeiro; empate resolvido pelo id para a resposta ser estável.
            ranqueados.sort(key=lambda r: (-r[0], r[1].id))

            recomendacoes = []
            for score, produto, motivo in ranqueados[:limite]:
                item = produto.to_dict()
                item["motivo_recomendacao"] = motivo
                recomendacoes.append(item)

            return {
                "success": True,
                "mensagem": "Recomendações geradas com sucesso.",
                "dados": {"base": ids, "restaurante_id": restaurant_id, "recomendacoes": recomendacoes},
            }
        except SQLAlchemyError:
            return RecommendationService._erro("Falha ao consultar o banco de dados.", 500)