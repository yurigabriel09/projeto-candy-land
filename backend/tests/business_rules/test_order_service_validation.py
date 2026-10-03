from app.services.order_service import OrderService, PAYMENT_METHODS


def test_pagamento_suporta_apenas_pix_e_cartao():
    assert PAYMENT_METHODS == {"PIX", "CARTAO_CREDITO"}


def test_metodo_de_pagamento_invalido_e_rejeitado():
    try:
        OrderService._validate_payment_method("BOLETO")
    except ValueError as exc:
        assert "PIX" in str(exc)
        assert "CARTAO_CREDITO" in str(exc)
    else:
        raise AssertionError("BOLETO deveria ser rejeitado no checkout")
