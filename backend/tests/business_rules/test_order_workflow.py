import pytest
from app.services.order_workflow_service import (
    OrderTransitionError,
    validar_transicao_entrega,
    validar_transicao_pedido,
)


def test_fluxo_principal_do_pedido():
    fluxo = [
        ("PENDENTE_PAGAMENTO", "PAGAMENTO_CONFIRMADO"),
        ("PAGAMENTO_CONFIRMADO", "RESTAURANTE_RECEBEU"),
        ("RESTAURANTE_RECEBEU", "RESTAURANTE_ACEITOU"),
        ("RESTAURANTE_ACEITOU", "PROCESSANDO"),
        ("PROCESSANDO", "PRONTO_PARA_ENTREGA"),
        ("PRONTO_PARA_ENTREGA", "ENTREGUE"),
        ("ENTREGUE", "FINALIZADO"),
    ]

    for atual, novo in fluxo:
        assert validar_transicao_pedido(atual, novo) is True


def test_pagamento_deve_vir_antes_da_baixa_do_estoque():
    assert (
        validar_transicao_pedido("PENDENTE_PAGAMENTO", "PAGAMENTO_CONFIRMADO") is True
    )
    with pytest.raises(OrderTransitionError):
        validar_transicao_pedido("PENDENTE_PAGAMENTO", "RESTAURANTE_RECEBEU")


def test_pedido_nao_pode_voltar_depois_de_finalizado():
    with pytest.raises(OrderTransitionError):
        validar_transicao_pedido("FINALIZADO", "PROCESSANDO")


def test_cancelamento_interrompe_producao():
    assert validar_transicao_pedido("PROCESSANDO", "CANCELADO") is True


def test_cancelamento_nao_ocorre_depois_de_entregue():
    with pytest.raises(OrderTransitionError):
        validar_transicao_pedido("ENTREGUE", "CANCELADO")


def test_motorista_pode_ser_encontrado_durante_a_producao():
    assert validar_transicao_pedido("RESTAURANTE_ACEITOU", "PROCESSANDO") is True
    assert validar_transicao_entrega("NAO_SOLICITADO", "PROCURANDO") is True
    assert validar_transicao_entrega("PROCURANDO", "MOTORISTA_ENCONTRADO") is True
    assert (
        validar_transicao_entrega("MOTORISTA_ENCONTRADO", "MOTORISTA_A_CAMINHO") is True
    )


def test_motorista_cancelado_retorna_para_busca():
    assert validar_transicao_entrega("MOTORISTA_A_CAMINHO", "PROCURANDO") is True


def test_transicao_de_entrega_invalida_e_rejeitada():
    with pytest.raises(OrderTransitionError):
        validar_transicao_entrega("PROCURANDO", "ENTREGA_CONCLUIDA")
