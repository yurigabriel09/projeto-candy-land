from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from app.database.database import db
from app.models.item_order import ItemPedido
from app.models.order import Pedido
from app.models.product import Produto
from app.models.restaurant import Restaurante
from app.utils.datetime_utils import (
    agora_brasilia,
    brasilia_para_utc_naive,
    inicio_do_dia_brasilia,
    utc_naive_para_brasilia,
)
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

# Só pedidos nesses status contam como venda (decisão do projeto).
STATUS_VENDA = ("ENTREGUE", "FINALIZADO")
# Pedidos que ainda não passaram do pagamento não são considerados "pedidos
# reais" (mesma regra da fila do restaurante em OrderService.listar_pedidos).
STATUS_NAO_PAGO = "PENDENTE_PAGAMENTO"

LIMITE_ESTOQUE_BAIXO = 5  # estoque <= 5 gera alerta
DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# Valor considerado "venda" de um pedido: produtos menos desconto, sem taxa de
# entrega nem taxa da plataforma. Para usar o total pago, troque por Pedido.total.
RECEITA_PEDIDO = Pedido.subtotal - Pedido.discount


def _num(valor, casas=2):
    return round(float(valor or 0), casas)


class ReportService:
    # ------------------------------------------------------------------ #
    # Janelas de tempo (calculadas em Brasília, convertidas p/ UTC naive)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _janela_mes(agora):
        inicio = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if inicio.month == 12:
            proximo = inicio.replace(year=inicio.year + 1, month=1)
        else:
            proximo = inicio.replace(month=inicio.month + 1)
        return brasilia_para_utc_naive(inicio), brasilia_para_utc_naive(proximo)

    @staticmethod
    def _janela_ano(agora):
        inicio = agora.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        proximo = inicio.replace(year=inicio.year + 1)
        return brasilia_para_utc_naive(inicio), brasilia_para_utc_naive(proximo)

    # ------------------------------------------------------------------ #
    # Consultas reutilizadas pelos relatórios
    # ------------------------------------------------------------------ #
    @staticmethod
    def _vendas_periodo(inicio, fim, restaurant_id=None):
        """Retorna (receita_total, qtd_pedidos) de vendas concluídas no período."""
        query = db.session.query(
            func.coalesce(func.sum(RECEITA_PEDIDO), 0), func.count(Pedido.id)
        ).filter(
            Pedido.status.in_(STATUS_VENDA),
            Pedido.created_at >= inicio,
            Pedido.created_at < fim,
        )
        if restaurant_id is not None:
            query = query.filter(Pedido.restaurant_id == restaurant_id)
        total, qtd = query.one()
        return total or 0, qtd or 0

    @staticmethod
    def _serie_ultimos_7_dias(agora, restaurant_id=None, contar_pedidos=False):
        """Série dos últimos 7 dias (incluindo hoje), agrupada por dia de Brasília.

        O agrupamento é feito em Python para respeitar o fuso e funcionar em
        qualquer banco (não depende de funções de data do SQLite).
        """
        hoje = inicio_do_dia_brasilia(agora)
        primeiro = hoje - timedelta(days=6)
        fim = hoje + timedelta(days=1)

        query = db.session.query(Pedido.created_at, RECEITA_PEDIDO).filter(
            Pedido.status.in_(STATUS_VENDA),
            Pedido.created_at >= brasilia_para_utc_naive(primeiro),
            Pedido.created_at < brasilia_para_utc_naive(fim),
        )
        if restaurant_id is not None:
            query = query.filter(Pedido.restaurant_id == restaurant_id)

        totais = defaultdict(Decimal)
        for criado_em, receita in query.all():
            dia = utc_naive_para_brasilia(criado_em).date()
            totais[dia] += Decimal(1) if contar_pedidos else Decimal(receita or 0)

        serie = []
        for i in range(7):
            dia = (primeiro + timedelta(days=i)).date()
            valor = totais.get(dia, Decimal(0))
            serie.append(
                {
                    "data": dia.isoformat(),
                    "dia_semana": DIAS_SEMANA[dia.weekday()],
                    ("pedidos" if contar_pedidos else "total"): (
                        int(valor) if contar_pedidos else _num(valor)
                    ),
                }
            )
        return serie

    @staticmethod
    def _top_produtos(inicio, fim, restaurant_id=None, limite=3):
        unidades = func.sum(ItemPedido.quantidade)
        receita = func.sum(ItemPedido.quantidade * ItemPedido.preco_unitario)
        query = (
            db.session.query(
                Produto.id,
                Produto.name,
                unidades.label("unidades"),
                receita.label("receita"),
            )
            .join(ItemPedido, ItemPedido.id_produto == Produto.id)
            .join(Pedido, Pedido.id == ItemPedido.id_pedido)
            .filter(
                Pedido.status.in_(STATUS_VENDA),
                Pedido.created_at >= inicio,
                Pedido.created_at < fim,
            )
        )
        if restaurant_id is not None:
            query = query.filter(Pedido.restaurant_id == restaurant_id)

        linhas = (
            query.group_by(Produto.id, Produto.name)
            .order_by(unidades.desc(), receita.desc())
            .limit(limite)
            .all()
        )
        return [
            {
                "posicao": posicao,
                "id_produto": linha.id,
                "nome_produto": linha.name,
                "unidades": int(linha.unidades or 0),
                "receita": _num(linha.receita),
            }
            for posicao, linha in enumerate(linhas, start=1)
        ]

    @staticmethod
    def _top_lojas(inicio, fim, limite=3):
        receita = func.sum(RECEITA_PEDIDO)
        linhas = (
            db.session.query(
                Restaurante.id,
                Restaurante.nome,
                receita.label("receita"),
                func.count(Pedido.id).label("pedidos"),
            )
            .join(Pedido, Pedido.restaurant_id == Restaurante.id)
            .filter(
                Pedido.status.in_(STATUS_VENDA),
                Pedido.created_at >= inicio,
                Pedido.created_at < fim,
            )
            .group_by(Restaurante.id, Restaurante.nome)
            .order_by(receita.desc())
            .limit(limite)
            .all()
        )
        return [
            {
                "posicao": posicao,
                "id_restaurante": linha.id,
                "nome": linha.nome,
                "pedidos": int(linha.pedidos or 0),
                "receita": _num(linha.receita),
            }
            for posicao, linha in enumerate(linhas, start=1)
        ]

    @staticmethod
    def _alertas_estoque(restaurant_id):
        # Obs.: não filtra por is_available; produtos desativados manualmente
        # também aparecem se o estoque estiver baixo.
        produtos = (
            Produto.query.filter(
                Produto.restaurant_id == restaurant_id,
                Produto.current_stock <= LIMITE_ESTOQUE_BAIXO,
            )
            .order_by(Produto.current_stock.asc(), Produto.name.asc())
            .all()
        )
        itens = [
            {
                "id_produto": p.id,
                "nome_produto": p.name,
                "qtd_estoque": p.current_stock,
                "status": "ESGOTADO" if p.current_stock <= 0 else "ESTOQUE_BAIXO",
            }
            for p in produtos
        ]
        return {"total": len(itens), "itens": itens}

    @staticmethod
    def _avaliacao_media():
        # TODO: implementar quando existir o model de avaliação, ex.:
        # from app.models.review import Avaliacao
        # media = db.session.query(func.avg(Avaliacao.nota)).scalar()
        # return round(float(media), 2) if media is not None else None
        return None

    # ------------------------------------------------------------------ #
    # Relatórios
    # ------------------------------------------------------------------ #
    @staticmethod
    def relatorio_loja(restaurant_id):
        try:
            agora = agora_brasilia()
            inicio_mes, fim_mes = ReportService._janela_mes(agora)

            vendas_mes, pedidos_mes = ReportService._vendas_periodo(
                inicio_mes, fim_mes, restaurant_id
            )
            media_dia = Decimal(vendas_mes) / agora.day  # dias decorridos no mês

            dados = {
                "gerado_em": agora.isoformat(),
                "cards": {
                    "vendas_mes": _num(vendas_mes),
                    "media_por_dia": _num(media_dia),
                    "pedidos": pedidos_mes,
                },
                "vendas_semana": ReportService._serie_ultimos_7_dias(
                    agora, restaurant_id
                ),
                "top_produtos": ReportService._top_produtos(
                    inicio_mes, fim_mes, restaurant_id
                ),
                "alertas_estoque": ReportService._alertas_estoque(restaurant_id),
            }
            return {
                "success": True,
                "mensagem": "Relatório da loja gerado.",
                "dados": dados,
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao gerar o relatório da loja.",
                "status_code": 500,
            }

    @staticmethod
    def relatorio_admin():
        try:
            agora = agora_brasilia()
            inicio_mes, fim_mes = ReportService._janela_mes(agora)
            inicio_ano, fim_ano = ReportService._janela_ano(agora)

            faturamento_mensal, _ = ReportService._vendas_periodo(
                inicio_mes, fim_mes
            )
            faturamento_anual, _ = ReportService._vendas_periodo(
                inicio_ano, fim_ano
            )
            media_dia = Decimal(faturamento_mensal) / agora.day

            # Pedidos concluídos (histórico completo) e taxa de sucesso =
            # concluídos / pedidos que passaram do pagamento.
            concluidos = (
                db.session.query(func.count(Pedido.id))
                .filter(Pedido.status.in_(STATUS_VENDA))
                .scalar()
                or 0
            )
            total_validos = (
                db.session.query(func.count(Pedido.id))
                .filter(Pedido.status != STATUS_NAO_PAGO)
                .scalar()
                or 0
            )
            taxa_sucesso = (
                round(concluidos / total_validos * 100, 1) if total_validos else None
            )

            lojas_ativas = (
                db.session.query(func.count(Restaurante.id))
                .filter(Restaurante.ativo.is_(True))
                .scalar()
                or 0
            )

            dados = {
                "gerado_em": agora.isoformat(),
                "cards": {
                    "media_por_dia": _num(media_dia),
                    "faturamento_mensal": _num(faturamento_mensal),
                    "faturamento_anual": _num(faturamento_anual),
                    "pedidos_concluidos": concluidos,
                    "taxa_sucesso_pct": taxa_sucesso,
                },
                "top_lojas": ReportService._top_lojas(inicio_mes, fim_mes),
                "top_produtos": ReportService._top_produtos(inicio_mes, fim_mes),
                "evolucao_plataforma": ReportService._serie_ultimos_7_dias(
                    agora, contar_pedidos=True
                ),
                "resumo_estrategico": {
                    "lojas_ativas": lojas_ativas,
                    "avaliacao_media": ReportService._avaliacao_media(),
                },
            }
            return {
                "success": True,
                "mensagem": "Relatório administrativo gerado.",
                "dados": dados,
            }
        except SQLAlchemyError:
            return {
                "success": False,
                "erro": "Falha ao gerar o relatório administrativo.",
                "status_code": 500,
            }
