"""Comprovante de compra em PDF (simulado, sem validade fiscal) e envio por e-mail.

Os dados vêm sempre do banco (pedido já persistido), nunca do frontend.
"""
import os
from datetime import timedelta, timezone
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.database.database import db
from app.models.address import Endereco
from app.models.item_order import ItemPedido
from app.models.order import Pedido
from app.models.product import Produto
from app.models.restaurant import Restaurante
from app.models.user import Usuario

ROSA = colors.HexColor("#f4356e")
MARROM = colors.HexColor("#4a1f1d")
CINZA = colors.HexColor("#9b7b75")
BORDA = colors.HexColor("#f2ddd2")

# Brasil não tem horário de verão desde 2019; evita depender de tzdata no Windows.
FUSO_BRASIL = timezone(timedelta(hours=-3))

# Mesmos status que o OrderService considera "pagamento já confirmado".
STATUS_COM_PAGAMENTO = {
    "PAGAMENTO_CONFIRMADO",
    "RESTAURANTE_RECEBEU",
    "RESTAURANTE_ACEITOU",
    "PROCESSANDO",
    "PRONTO_PARA_ENTREGA",
    "ENTREGUE",
    "FINALIZADO",
}

FORMAS_PAGAMENTO = {
    "PIX": "Pix",
    "PAYPAL": "PayPal",
    "MERCADO_PAGO": "Mercado Pago",
    "CARTAO": "Cartão",
    "CARTAO_CREDITO": "Cartão de crédito",
    "CARTAO_DEBITO": "Cartão de débito",
    "BOLETO": "Boleto",
}
TIPOS_PEDIDO = {"DELIVERY": "Entrega", "PICKUP": "Retirada na loja"}


def formatar_moeda(valor):
    numero = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    texto = f"{numero:,.2f}"  # 1,234.50
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _mascarar_cpf(cpf):
    digitos = "".join(c for c in str(cpf or "") if c.isdigit())
    if len(digitos) != 11:
        return "—"
    return f"***.{digitos[3:6]}.{digitos[6:9]}-**"


def _mascarar_email(email):
    usuario, _, dominio = str(email or "").partition("@")
    if not usuario or not dominio:
        return "seu e-mail cadastrado"
    return f"{usuario[0]}***@{dominio}"


def _endereco_texto(endereco):
    if not endereco:
        return "—"
    linha1 = ", ".join(p for p in [endereco.rua, endereco.numero, endereco.complemento] if p)
    linha2 = " - ".join(p for p in [endereco.bairro, f"{endereco.cidade}/{endereco.estado}"] if p)
    return f"{linha1}, {linha2}, CEP {endereco.cep}"


def montar_dados(pedido_id):
    """Lê o pedido e tudo o que a nota precisa. Retorna None se não existir."""
    pedido = db.session.get(Pedido, pedido_id)
    if not pedido:
        return None
    cliente = db.session.get(Usuario, pedido.user_id)
    loja = db.session.get(Restaurante, pedido.restaurant_id)

    endereco_loja = None
    if loja:
        if loja.address_id:
            endereco_loja = db.session.get(Endereco, loja.address_id)
        if not endereco_loja:
            endereco_loja = Endereco.query.filter_by(
                id_restaurante=loja.id, ativo=True
            ).first()
    endereco_destino = db.session.get(Endereco, pedido.delivery_address_id)

    itens = []
    for item in ItemPedido.query.filter_by(id_pedido=pedido.id).all():
        produto = db.session.get(Produto, item.id_produto)
        itens.append(
            {
                "nome": produto.name if produto else f"Produto #{item.id_produto}",
                "quantidade": item.quantidade,
                "preco_unitario": Decimal(str(item.preco_unitario)),
                "observacoes": item.observacoes,
            }
        )

    criado = pedido.created_at
    if criado is not None:
        criado = criado.replace(tzinfo=timezone.utc).astimezone(FUSO_BRASIL)

    return {
        "codigo": pedido.order_code,
        "criado_em": criado,
        "tipo": TIPOS_PEDIDO.get(pedido.order_type, pedido.order_type),
        "eh_entrega": pedido.order_type == "DELIVERY",
        "pagamento": FORMAS_PAGAMENTO.get(pedido.payment_method, pedido.payment_method),
        "observacao": pedido.general_note,
        "subtotal": pedido.subtotal,
        "desconto": pedido.discount,
        "taxa_entrega": pedido.delivery_fee,
        "taxa_plataforma": pedido.platform_fee,
        "total": pedido.total,
        "cliente_nome": cliente.nome_completo if cliente else "—",
        "cliente_email": cliente.email if cliente else None,
        "cliente_cpf": _mascarar_cpf(cliente.cpf) if cliente else "—",
        "loja_nome": loja.nome if loja else "—",
        "loja_razao_social": loja.razao_social if loja else "—",
        "loja_cnpj": loja.cnpj if loja else "—",
        "loja_endereco": _endereco_texto(endereco_loja),
        "destino_endereco": _endereco_texto(endereco_destino),
        "itens": itens,
    }


def gerar_pdf(dados):
    """Gera o PDF em memória e devolve os bytes."""
    estilos = getSampleStyleSheet()
    normal = ParagraphStyle("normal", parent=estilos["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=MARROM)
    suave = ParagraphStyle("suave", parent=normal, textColor=CINZA, fontSize=8.5)
    titulo = ParagraphStyle("titulo", parent=normal, fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=ROSA)
    secao = ParagraphStyle("secao", parent=normal, fontName="Helvetica-Bold", fontSize=11, textColor=ROSA, spaceBefore=10, spaceAfter=4)

    def p(texto, estilo=normal):
        return Paragraph(escape(str(texto)), estilo)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Comprovante {dados['codigo']}", author="CandyLand",
    )
    largura = A4[0] - 36 * mm
    historia = [
        Paragraph("CandyLand", titulo),
        p("Comprovante de compra — documento sem valor fiscal", suave),
        Spacer(1, 6),
    ]

    data = dados["criado_em"].strftime("%d/%m/%Y %H:%M") if dados["criado_em"] else "—"
    historia += [
        Paragraph("Pedido", secao),
        p(f"Código: {dados['codigo']}"),
        p(f"Data: {data}"),
        p(f"Tipo: {dados['tipo']}"),
        p(f"Forma de pagamento: {dados['pagamento']}"),
        Paragraph("Loja", secao),
        p(dados["loja_nome"]),
        p(f"{dados['loja_razao_social']} — CNPJ {dados['loja_cnpj']}"),
        p(dados["loja_endereco"], suave),
        Paragraph("Cliente", secao),
        p(f"{dados['cliente_nome']} — CPF {dados['cliente_cpf']}"),
    ]
    if dados["eh_entrega"]:
        historia.append(p(f"Entrega em: {dados['destino_endereco']}", suave))
    else:
        historia.append(p(f"Retirada em: {dados['destino_endereco']}", suave))

    historia.append(Paragraph("Itens", secao))
    linhas = [["Item", "Qtd", "Preço unit.", "Total"]]
    for item in dados["itens"]:
        total_item = item["preco_unitario"] * item["quantidade"]
        nome = escape(item["nome"])
        if item.get("observacoes"):
            nome += f"<br/><font size=8 color='#9b7b75'>Obs.: {escape(item['observacoes'])}</font>"
        linhas.append([Paragraph(nome, normal), str(item["quantidade"]), formatar_moeda(item["preco_unitario"]), formatar_moeda(total_item)])
    tabela = Table(linhas, colWidths=[largura * 0.52, largura * 0.1, largura * 0.19, largura * 0.19], repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ROSA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    historia.append(tabela)

    resumo = [["Subtotal", formatar_moeda(dados["subtotal"])]]
    if Decimal(str(dados["desconto"] or 0)) > 0:
        resumo.append(["Desconto", "- " + formatar_moeda(dados["desconto"])])
    resumo.append(["Taxa de entrega", formatar_moeda(dados["taxa_entrega"])])
    if Decimal(str(dados["taxa_plataforma"] or 0)) > 0:
        resumo.append(["Taxa da plataforma", formatar_moeda(dados["taxa_plataforma"])])
    resumo.append(["TOTAL", formatar_moeda(dados["total"])])
    tabela_resumo = Table(resumo, colWidths=[largura * 0.7, largura * 0.3], hAlign="RIGHT")
    tabela_resumo.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), MARROM),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("TEXTCOLOR", (0, -1), (-1, -1), ROSA),
        ("LINEABOVE", (0, -1), (-1, -1), 1, ROSA),
    ]))
    historia += [Spacer(1, 8), tabela_resumo]

    if dados.get("observacao"):
        historia += [Paragraph("Observação do pedido", secao), p(dados["observacao"])]

    historia += [
        Spacer(1, 18),
        p("Este documento é apenas um comprovante da compra feita na plataforma CandyLand "
          "e não substitui a nota fiscal eletrônica (NF-e).", suave),
    ]
    doc.build(historia)
    return buffer.getvalue()


class InvoiceService:
    @staticmethod
    def gerar_pdf_do_pedido(pedido_id):
        """Retorna (bytes_do_pdf, codigo_do_pedido) ou (None, None)."""
        dados = montar_dados(pedido_id)
        if not dados:
            return None, None
        return gerar_pdf(dados), dados["codigo"]

    @staticmethod
    def _pedido_liberado(pedido_id, account_id, account_type):
        """Só o cliente dono do pedido, e só depois do pagamento confirmado."""
        if account_type != "PERSONAL":
            return None, {"success": False, "erro": "Apenas o cliente pode acessar o comprovante.", "status_code": 403}
        pedido = db.session.get(Pedido, pedido_id)
        if not pedido:
            return None, {"success": False, "erro": "Pedido não encontrado.", "status_code": 404}
        if pedido.user_id != account_id:
            return None, {"success": False, "erro": "Você não tem acesso a este pedido.", "status_code": 403}
        if pedido.status not in STATUS_COM_PAGAMENTO:
            return None, {
                "success": False,
                "erro": "O comprovante só fica disponível depois da confirmação do pagamento.",
                "status_code": 409,
            }
        return pedido, None

    @staticmethod
    def baixar(pedido_id, account_id, account_type):
        pedido, erro = InvoiceService._pedido_liberado(pedido_id, account_id, account_type)
        if erro:
            return erro
        pdf, codigo = InvoiceService.gerar_pdf_do_pedido(pedido.id)
        return {"success": True, "pdf": pdf, "nome_arquivo": f"comprovante-{codigo}.pdf"}

    @staticmethod
    def reenviar(pedido_id, account_id, account_type):
        pedido, erro = InvoiceService._pedido_liberado(pedido_id, account_id, account_type)
        if erro:
            return erro
        try:
            return InvoiceService.enviar_por_email(pedido.id)
        except ValueError:
            return {
                "success": False,
                "erro": "Não foi possível enviar o e-mail agora. Tente novamente em instantes.",
                "status_code": 502,
            }

    @staticmethod
    def email_configurado():
        return bool(os.getenv("BREVO_API_KEY") and os.getenv("BREVO_SENDER_EMAIL"))

    @staticmethod
    def enviar_por_email(pedido_id):
        """Gera o comprovante e envia ao e-mail do cliente. Levanta ValueError se falhar."""
        # Import tardio: evita ciclo e mantém este módulo testável sem o Brevo.
        from app.services.email_service import EmailService

        if not InvoiceService.email_configurado():
            return {"success": False, "erro": "Configuração do Brevo não encontrada.", "status_code": 503}
        dados = montar_dados(pedido_id)
        if not dados:
            return {"success": False, "erro": "Pedido não encontrado.", "status_code": 404}
        if not dados["cliente_email"]:
            return {"success": False, "erro": "Cliente sem e-mail cadastrado.", "status_code": 409}
        pdf = gerar_pdf(dados)
        EmailService.enviar_comprovante(
            dados["cliente_email"], dados["cliente_nome"], dados["codigo"], pdf
        )
        return {
            "success": True,
            "mensagem": f"Comprovante enviado para {_mascarar_email(dados['cliente_email'])}.",
        }