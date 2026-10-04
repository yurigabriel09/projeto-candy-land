class OrderTransitionError(ValueError):
    """Indica que uma transição de pedido não é permitida."""


ORDER_STATUSES = {
    "PENDENTE_PAGAMENTO",
    "PAGAMENTO_CONFIRMADO",
    "RESTAURANTE_RECEBEU",
    "RESTAURANTE_ACEITOU",
    "PROCESSANDO",
    "PRONTO_PARA_ENTREGA",
    "ENTREGUE",
    "FINALIZADO",
    "CANCELADO",
}

DELIVERY_STATUSES = {
    "NAO_SOLICITADO",
    "PROCURANDO",
    "MOTORISTA_ENCONTRADO",
    "MOTORISTA_A_CAMINHO",
    "MOTORISTA_NO_RESTAURANTE",
    "PEDIDO_RETIRADO",
    "EM_ROTA",
    "ENTREGA_CONCLUIDA",
    "SEM_MOTORISTA",
    "CANCELADO",
}

ORDER_TRANSITIONS = {
    "PENDENTE_PAGAMENTO": {"PAGAMENTO_CONFIRMADO", "CANCELADO"},
    "PAGAMENTO_CONFIRMADO": {"RESTAURANTE_RECEBEU", "CANCELADO"},
    "RESTAURANTE_RECEBEU": {"RESTAURANTE_ACEITOU", "CANCELADO"},
    "RESTAURANTE_ACEITOU": {"PROCESSANDO", "CANCELADO"},
    "PROCESSANDO": {"PRONTO_PARA_ENTREGA", "CANCELADO"},
    "PRONTO_PARA_ENTREGA": {"ENTREGUE", "CANCELADO"},
    "ENTREGUE": {"FINALIZADO"},
    "FINALIZADO": set(),
    "CANCELADO": set(),
}

DELIVERY_TRANSITIONS = {
    "NAO_SOLICITADO": {"PROCURANDO", "CANCELADO"},
    "PROCURANDO": {"MOTORISTA_ENCONTRADO", "SEM_MOTORISTA", "CANCELADO"},
    "MOTORISTA_ENCONTRADO": {"MOTORISTA_A_CAMINHO", "PROCURANDO", "CANCELADO"},
    "MOTORISTA_A_CAMINHO": {"MOTORISTA_NO_RESTAURANTE", "PROCURANDO", "CANCELADO"},
    "MOTORISTA_NO_RESTAURANTE": {"PEDIDO_RETIRADO", "PROCURANDO", "CANCELADO"},
    "PEDIDO_RETIRADO": {"EM_ROTA", "CANCELADO"},
    "EM_ROTA": {"ENTREGA_CONCLUIDA", "CANCELADO"},
    "ENTREGA_CONCLUIDA": set(),
    "SEM_MOTORISTA": {"PROCURANDO", "CANCELADO"},
    "CANCELADO": set(),
}


def validar_status_pedido(status):
    if status not in ORDER_STATUSES:
        raise OrderTransitionError(f"Status de pedido inválido: {status}.")


def validar_status_entrega(status):
    if status not in DELIVERY_STATUSES:
        raise OrderTransitionError(f"Status de entrega inválido: {status}.")


def validar_transicao_pedido(status_atual, novo_status):
    validar_status_pedido(status_atual)
    validar_status_pedido(novo_status)

    if novo_status not in ORDER_TRANSITIONS[status_atual]:
        raise OrderTransitionError(
            f"Transição de pedido não permitida: {status_atual} -> {novo_status}."
        )

    return True


def validar_transicao_entrega(status_atual, novo_status):
    validar_status_entrega(status_atual)
    validar_status_entrega(novo_status)

    if novo_status not in DELIVERY_TRANSITIONS[status_atual]:
        raise OrderTransitionError(
            f"Transição de entrega não permitida: {status_atual} -> {novo_status}."
        )

    return True
