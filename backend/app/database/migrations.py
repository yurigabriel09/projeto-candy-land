"""Migrações aditivas e seguras do schema CandyLand.

As migrações verificam as colunas antes de alterá-las e não removem dados.
"""
from sqlalchemy import inspect, text


def migrar_taxa_entrega_por_distancia(engine):
    """Adiciona colunas da taxa por distância em bancos já existentes.

    Funciona com SQLite e PostgreSQL. O modelo ORM e db.create_all() não
    adicionam colunas a tabelas que já existem, então esta migração deve rodar
    antes de qualquer consulta que selecione os novos campos.
    """
    inspector = inspect(engine)
    tabelas = set(inspector.get_table_names())
    necessarias = {"restaurants", "orders"}
    ausentes = necessarias - tabelas
    if ausentes:
        raise RuntimeError(
            "Não foi possível migrar taxa de entrega: tabelas ausentes: "
            + ", ".join(sorted(ausentes))
        )

    novas_colunas = {
        "restaurants": {
            "taxa_entrega_por_km":
                "NUMERIC(10, 2) NOT NULL DEFAULT 0",
        },
        "orders": {
            "delivery_distance_km": "NUMERIC(8, 2) NULL",
        },
    }
    alteracoes = []
    for tabela, colunas in novas_colunas.items():
        existentes = {coluna["name"] for coluna in inspect(engine).get_columns(tabela)}
        for coluna, definicao in colunas.items():
            if coluna not in existentes:
                alteracoes.append((tabela, coluna, definicao))

    if not alteracoes:
        return []

    with engine.begin() as connection:
        for tabela, coluna, definicao in alteracoes:
            # Nomes são constantes definidos acima, não valores recebidos do usuário.
            connection.execute(
                text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
            )
    return [f"{tabela}.{coluna}" for tabela, coluna, _ in alteracoes]
