from app.models.restaurant import Restaurante


def test_catalogo_publico_inclui_ativo_em_booleano_para_home():
    restaurante = Restaurante(
        cnpj="12345678000190",
        razao_social="Doceria Teste LTDA",
        nome="Doceria Teste",
        cpf_responsavel="98765432100",
        email="catalogo-teste@example.com",
        telefone="+551133334444",
        ativo=True,
    )
    publico = restaurante.to_catalog_dict()
    assert publico["ativo"] is True
    assert "cnpj" not in publico
    assert "email" not in publico
    assert "telefone" not in publico
