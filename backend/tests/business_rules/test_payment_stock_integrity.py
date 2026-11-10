import pytest
from flask import Flask

from app.database.database import db
from app.models import (
    Categoria,
    Endereco,
    EntregaPedido,
    ItemPedido,
    Pedido,
    Produto,
    Restaurante,
    Usuario,
)
from app.services.order_service import OrderService


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="test-secret-key",
        JWT_EXPIRATION_HOURS=1,
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def _criar_cenario(status="PENDENTE_PAGAMENTO", estoque=10, itens=None):
    usuario = Usuario(
        nome_completo="Cliente de Teste",
        email="cliente-stock@example.com",
        telefone="+5511999991000",
        cpf="12345678901",
    )
    restaurante = Restaurante(
        cnpj="12345678000190",
        razao_social="Doceria Stock LTDA",
        nome="Doceria Stock",
        cpf_responsavel="98765432100",
        email="doceria-stock@example.com",
        telefone="+5511888881000",
        taxa_entrega_base=0,
        taxa_entrega_por_km=0,
        raio_entrega_km=10,
    )
    db.session.add_all([usuario, restaurante])
    db.session.commit()

    endereco = Endereco(
        id_usuario=usuario.id,
        cep="01001000",
        rua="Rua de Teste",
        numero="10",
        bairro="Centro",
        cidade="São Paulo",
        estado="SP",
        tipo_endereco="RESIDENCIAL",
        principal=True,
        ativo=True,
    )
    categoria = Categoria(
        id_restaurante=restaurante.id,
        nome="Doces de Teste",
        descricao="Categoria para teste de estoque",
    )
    db.session.add_all([endereco, categoria])
    db.session.commit()

    produto_principal = Produto(
        restaurant_id=restaurante.id,
        category_id=categoria.id,
        name="Bolo de Teste",
        description="Produto para teste transacional",
        price=10,
        is_available=True,
        is_imported=False,
        current_stock=estoque,
        allows_customization=False,
    )
    db.session.add(produto_principal)
    db.session.commit()

    produtos = {produto_principal.id: produto_principal}
    linhas = itens if itens is not None else [(produto_principal, 2)]
    subtotal = 0
    for produto, quantidade in linhas:
        subtotal += float(produto.price) * quantidade

    pedido = Pedido(
        order_code=f"CL-STOCK-{usuario.id:04d}",
        user_id=usuario.id,
        restaurant_id=restaurante.id,
        delivery_address_id=endereco.id,
        subtotal=subtotal,
        discount=0,
        delivery_fee=0,
        platform_fee=0,
        total=subtotal,
        order_type="DELIVERY",
        status=status,
        payment_method="PIX",
    )
    db.session.add(pedido)
    db.session.flush()
    db.session.add(EntregaPedido(pedido_id=pedido.id))
    for produto, quantidade in linhas:
        db.session.add(
            ItemPedido(
                id_pedido=pedido.id,
                id_produto=produto.id,
                quantidade=quantidade,
                preco_unitario=produto.price,
            )
        )
        produtos[produto.id] = produto
    db.session.commit()
    return pedido, usuario, restaurante, produtos


def test_confirmar_pagamento_repetido_nao_debita_estoque_duas_vezes(app):
    with app.app_context():
        pedido, _, _, produtos = _criar_cenario(estoque=10)
        produto = produtos[next(iter(produtos))]

        primeira = OrderService.confirmar_pagamento(pedido.id)
        db.session.refresh(produto)
        db.session.refresh(pedido)
        assert primeira["success"] is True
        assert pedido.status == "PAGAMENTO_CONFIRMADO"
        assert produto.current_stock == 8

        segunda = OrderService.confirmar_pagamento(pedido.id)
        db.session.refresh(produto)
        db.session.refresh(pedido)
        assert segunda["success"] is True
        assert "já confirmado" in segunda["mensagem"].lower()
        assert pedido.status == "PAGAMENTO_CONFIRMADO"
        assert produto.current_stock == 8


def test_confirmacao_com_estoque_insuficiente_reverte_status_e_todas_as_baixas(app):
    with app.app_context():
        pedido, _, restaurante, produtos = _criar_cenario(estoque=10)
        categoria = Categoria.query.filter_by(id_restaurante=restaurante.id).first()
        produto_sem_estoque = Produto(
            restaurant_id=restaurante.id,
            category_id=categoria.id,
            name="Produto sem estoque",
            description="Deve provocar rollback",
            price=5,
            is_available=True,
            is_imported=False,
            current_stock=0,
            allows_customization=False,
        )
        db.session.add(produto_sem_estoque)
        db.session.flush()
        db.session.add(
            ItemPedido(
                id_pedido=pedido.id,
                id_produto=produto_sem_estoque.id,
                quantidade=1,
                preco_unitario=5,
            )
        )
        db.session.commit()
        produtos[produto_sem_estoque.id] = produto_sem_estoque
        produto_principal = next(p for p in produtos.values() if p.name == "Bolo de Teste")

        resultado = OrderService.confirmar_pagamento(pedido.id)

        db.session.refresh(pedido)
        db.session.refresh(produto_principal)
        db.session.refresh(produto_sem_estoque)
        assert resultado["success"] is False
        assert resultado["status_code"] == 409
        assert pedido.status == "PENDENTE_PAGAMENTO"
        assert produto_principal.current_stock == 10
        assert produto_sem_estoque.current_stock == 0


def test_cancelamento_do_cliente_repoe_estoque_uma_unica_vez(app):
    with app.app_context():
        pedido, usuario, _, produtos = _criar_cenario(
            status="PAGAMENTO_CONFIRMADO", estoque=8
        )
        produto = next(iter(produtos.values()))

        primeira = OrderService.cancelar_pedido(pedido.id, usuario.id)
        db.session.refresh(produto)
        db.session.refresh(pedido)
        entrega = EntregaPedido.query.filter_by(pedido_id=pedido.id).first()
        assert primeira["success"] is True
        assert pedido.status == "CANCELADO"
        assert produto.current_stock == 10
        assert entrega.status == "CANCELADO"

        segunda = OrderService.cancelar_pedido(pedido.id, usuario.id)
        db.session.refresh(produto)
        assert segunda["success"] is False
        assert segunda["status_code"] == 409
        assert produto.current_stock == 10


def test_cancelamento_do_restaurante_repoe_estoque_uma_unica_vez(app):
    with app.app_context():
        pedido, _, restaurante, produtos = _criar_cenario(
            status="PROCESSANDO", estoque=8
        )
        produto = next(iter(produtos.values()))

        primeira = OrderService.atualizar_status(
            pedido.id, "CANCELADO", restaurante.id, "BUSINESS"
        )
        db.session.refresh(pedido)
        db.session.refresh(produto)
        assert primeira["success"] is True
        assert pedido.status == "CANCELADO"
        assert produto.current_stock == 10

        segunda = OrderService.atualizar_status(
            pedido.id, "CANCELADO", restaurante.id, "BUSINESS"
        )
        db.session.refresh(produto)
        assert segunda["success"] is False
        assert segunda["status_code"] == 409
        assert produto.current_stock == 10


def test_cancelamento_antes_do_pagamento_nao_altera_estoque(app):
    with app.app_context():
        pedido, usuario, _, produtos = _criar_cenario(
            status="PENDENTE_PAGAMENTO", estoque=10
        )
        produto = next(iter(produtos.values()))

        resultado = OrderService.cancelar_pedido(pedido.id, usuario.id)

        db.session.refresh(pedido)
        db.session.refresh(produto)
        assert resultado["success"] is True
        assert pedido.status == "CANCELADO"
        assert produto.current_stock == 10


def test_reenvio_de_confirmacao_apos_inicio_operacional_nao_altera_estoque(app):
    with app.app_context():
        pedido, _, restaurante, produtos = _criar_cenario(estoque=10)
        produto = next(iter(produtos.values()))

        pagamento = OrderService.confirmar_pagamento(pedido.id)
        assert pagamento["success"] is True
        inicio = OrderService.atualizar_status(
            pedido.id, "RESTAURANTE_RECEBEU", restaurante.id, "BUSINESS"
        )
        assert inicio["success"] is True

        repeticao = OrderService.confirmar_pagamento(pedido.id)
        db.session.refresh(pedido)
        db.session.refresh(produto)
        assert repeticao["success"] is True
        assert pedido.status == "RESTAURANTE_RECEBEU"
        assert produto.current_stock == 8
