import os
import uuid
from pathlib import Path

from flask import current_app


def _detectar_tipo(cabecalho):
    if cabecalho.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if cabecalho.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if cabecalho[:4] == b"RIFF" and cabecalho[8:12] == b"WEBP":
        return "webp"
    return None


def _pasta_do_restaurante(restaurant_id):
    base = Path(current_app.config["UPLOAD_FOLDER"])
    return base / "restaurantes" / str(restaurant_id)


def salvar_imagem_produto(arquivo, restaurant_id):
    """Valida e grava a imagem. Retorna o caminho relativo para guardar no banco."""
    stream = arquivo.stream

    stream.seek(0, os.SEEK_END)
    tamanho = stream.tell()
    stream.seek(0)

    if tamanho == 0:
        raise ValueError("O arquivo enviado está vazio.")
    if tamanho > current_app.config["UPLOAD_MAX_BYTES"]:
        raise ValueError("A imagem passa de 2 MB. Escolha um arquivo menor.")

    tipo = _detectar_tipo(stream.read(12))
    stream.seek(0)
    if tipo is None:
        raise ValueError("Formato inválido. Envie uma imagem JPG, PNG ou WEBP.")

    pasta = _pasta_do_restaurante(restaurant_id)
    pasta.mkdir(parents=True, exist_ok=True)

    # Nome gerado pelo backend: nunca usamos o nome original do arquivo
    nome_arquivo = f"{uuid.uuid4().hex}.{tipo}"
    arquivo.save(pasta / nome_arquivo)

    return f"/uploads/restaurantes/{restaurant_id}/{nome_arquivo}"


def remover_imagem(image_url, restaurant_id):
    """Apaga o arquivo, mas só se estiver dentro da pasta do próprio restaurante."""
    if not image_url or not image_url.startswith("/uploads/restaurantes/"):
        return

    base = Path(current_app.config["UPLOAD_FOLDER"])
    caminho = (base / image_url[len("/uploads/"):]).resolve()
    pasta_dono = _pasta_do_restaurante(restaurant_id).resolve()

    if pasta_dono not in caminho.parents:
        return

    try:
        caminho.unlink(missing_ok=True)
    except OSError:
        pass  # falhar ao apagar uma foto antiga não deve quebrar a requisição