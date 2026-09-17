import re

def normalizar_telefone(telefone):
    if not telefone:
        return telefone

    apenas_digitos = re.sub(r"\D", "", telefone)

    if not apenas_digitos.startswith("55"):
        apenas_digitos = "55" + apenas_digitos

    return f"+{apenas_digitos}"