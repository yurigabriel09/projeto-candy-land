from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


def read(root: Path, rel: str) -> str:
    path = root / rel
    if not path.is_file():
        raise RuntimeError(f"Arquivo não encontrado: {rel}")
    return path.read_text(encoding="utf-8")


def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count == 0 and new in content:
        return content  # já aplicado
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1 trecho original, encontrado {count}.")
    return content.replace(old, new, 1)


def replace_in_function(content: str, function_name: str, old: str, new: str, label: str) -> str:
    start = content.find(function_name)
    if start < 0:
        raise RuntimeError(f"{label}: função não encontrada.")
    next_def = content.find("\ndef ", start + len(function_name))
    end = next_def if next_def >= 0 else len(content)
    block = content[start:end]
    updated = replace_once(block, old, new, label)
    return content[:start] + updated + content[end:]


def pix_order_fixture(order_id: str, amount: str, code: str, base64: str, ticket: str) -> str:
    return f'''{{
        "id": "ORD-PIX-{order_id}",
        "external_reference": "{order_id}",
        "status": "action_required",
        "status_detail": "waiting_transfer",
        "total_amount": "{amount}",
        "transactions": {{"payments": [{{
            "amount": "{amount}",
            "status": "action_required",
            "status_detail": "waiting_transfer",
            "payment_method": {{
                "id": "pix",
                "qr_code": "{code}",
                "qr_code_base64": "{base64}",
                "ticket_url": "{ticket}"
            }}
        }}]}}
    }}'''


def patch(root: Path) -> list[str]:
    changes: dict[str, str] = {}

    # 1) Logging bug: one %s placeholder was receiving two arguments, and the
    # provider's response body should not be logged at all.
    rel = "backend/app/services/email_service.py"
    s = read(root, rel)
    s = replace_once(
        s,
        '''                "Brevo recusou o envio de OTP (HTTP %s).",\n                response.text[:500],\n                response.status_code,\n''',
        '''                "Brevo recusou o envio de OTP (HTTP %s).",\n                response.status_code,\n''',
        "corrigir logging do Brevo",
    )
    changes[rel] = s

    # 2) Protect user deletion with authentication and ownership (the route was public).
    rel = "backend/app/routes/user_routes.py"
    s = read(root, rel)
    s = replace_once(
        s,
        '''@user_bp.route("/<int:user_id>", methods=["DELETE"])\ndef deletar_usuario(user_id):\n''',
        '''@user_bp.route("/<int:user_id>", methods=["DELETE"])\n@token_required\n@account_owner_required("PERSONAL", "user_id")\ndef deletar_usuario(user_id):\n''',
        "proteger exclusão do usuário",
    )
    changes[rel] = s

    # 3) Protect restaurant deletion with authenticated owner role.
    rel = "backend/app/routes/restaurant_routes.py"
    s = read(root, rel)
    s = replace_once(
        s,
        '''@restaurante_bp.route("/<int:restaurante_id>", methods=["DELETE"])\ndef deletar_restaurante(restaurante_id):\n''',
        '''@restaurante_bp.route("/<int:restaurante_id>", methods=["DELETE"])\n@token_required\n@account_owner_required("BUSINESS", "restaurante_id")\ndef deletar_restaurante(restaurante_id):\n''',
        "proteger exclusão da doceria",
    )
    changes[rel] = s

    # 4) Remove exact stock quantity from public catalog; private to_dict stays unchanged.
    rel = "backend/app/models/product.py"
    s = read(root, rel)
    s = replace_once(
        s,
        '''            "produto_disponivel": self.is_available,\n            "produto_importado": self.is_imported,\n            "qtd_estoque": self.current_stock,\n            "permite_personalizacao": self.allows_customization,\n''',
        '''            "produto_disponivel": self.is_available,\n            "produto_importado": self.is_imported,\n            "permite_personalizacao": self.allows_customization,\n''',
        "remover estoque do catálogo público",
    )
    changes[rel] = s

    # 5) Isolate account identity tests from the real Google Geocoding service.
    rel = "backend/tests/authentication/test_account_identity.py"
    s = read(root, rel)
    s = replace_once(
        s,
        '''def test_cadastro_pessoal_com_celular_do_restaurante_respeita_ambiente(\n    app, ambiente, deve_criar\n):\n''',
        '''def test_cadastro_pessoal_com_celular_do_restaurante_respeita_ambiente(\n    app, ambiente, deve_criar, monkeypatch\n):\n''',
        "fixture geocoding do cadastro pessoal",
    )
    s = replace_in_function(
        s,
        "def test_cadastro_pessoal_com_celular_do_restaurante_respeita_ambiente(",
        '''        resultado = UserService.criar_usuario(\n''',
        '''        monkeypatch.setattr(\n            "app.services.user_service.GeocodingService.geocodificar",\n            lambda _endereco: {"success": True, "dados": {"latitude": -23.55052, "longitude": -46.633308}},\n        )\n        resultado = UserService.criar_usuario(\n''',
        "mock geocoding do cadastro pessoal",
    )
    s = replace_once(
        s,
        '''def test_cadastro_de_restaurante_com_celular_do_cliente_respeita_ambiente(\n    app, ambiente, deve_criar\n):\n''',
        '''def test_cadastro_de_restaurante_com_celular_do_cliente_respeita_ambiente(\n    app, ambiente, deve_criar, monkeypatch\n):\n''',
        "fixture geocoding do cadastro comercial",
    )
    s = replace_in_function(
        s,
        "def test_cadastro_de_restaurante_com_celular_do_cliente_respeita_ambiente(",
        '''        resultado = RestauranteService.criar_restaurante(\n''',
        '''        monkeypatch.setattr(\n            "app.services.restaurant_service.GeocodingService.geocodificar",\n            lambda _endereco: {"success": True, "dados": {"latitude": -23.55052, "longitude": -46.633308}},\n        )\n        resultado = RestauranteService.criar_restaurante(\n''',
        "mock geocoding do cadastro comercial",
    )
    changes[rel] = s

    # 6) The restaurant configuration unit test should not call an external API.
    rel = "backend/tests/business_rules/test_restaurant_configuration.py"
    s = read(root, rel)
    s = replace_once(
        s,
        '''def test_atualizar_configuracao_cria_endereco_antes_do_flush(app):\n    with app.app_context():\n        restaurante = _criar_restaurante()\n''',
        '''def test_atualizar_configuracao_cria_endereco_antes_do_flush(app, monkeypatch):\n    with app.app_context():\n        monkeypatch.setattr(\n            "app.services.restaurant_service.GeocodingService.geocodificar",\n            lambda _endereco: {"success": True, "dados": {"latitude": -23.55052, "longitude": -46.633308}},\n        )\n        restaurante = _criar_restaurante()\n''',
        "isolar teste de configuração de restaurante",
    )
    changes[rel] = s

    # 7) Checkout tests must represent a shop that is open; production guard remains intact.
    rel = "backend/tests/checkout/test_checkout_api.py"
    s = read(root, rel)
    s = replace_once(
        s,
        '''        email="restaurante-checkout@example.com",\n        telefone="+551133334444",\n        taxa_entrega_base=Decimal("3.50"),\n''',
        '''        email="restaurante-checkout@example.com",\n        telefone="+551133334444",\n        status="ABERTO",\n        taxa_entrega_base=Decimal("3.50"),\n''',
        "abrir restaurante nas fixtures de checkout",
    )
    changes[rel] = s

    # 8) Test Pix adapter against the current Orders API contract, not the legacy Payments API.
    rel = "backend/tests/business_rules/test_mercado_pago_adapter.py"
    s = read(root, rel)
    marker = "def test_create_pix_retorna_qr_code_e_copia_e_cola(monkeypatch):"
    start = s.find(marker)
    if start < 0:
        if "def test_create_pix_usa_orders_api_e_retorna_qr_code" in s:
            pass
        else:
            raise RuntimeError("teste de Pix do adaptador Mercado Pago não encontrado")
    else:
        replacement = f'''def test_create_pix_usa_orders_api_e_retorna_qr_code(monkeypatch):
    chamadas = []
    ordem = {pix_order_fixture("17", "35.50", "000201PIX-COPIA-E-COLA-TESTE", "aVZCT1J3MEtHZ29BQUFBTlNVaEVVZ0FBQUFB", "https://www.mercadopago.com.br/pix/17")}

    def fake_request(method, url, **kwargs):
        chamadas.append((method, url, kwargs))
        return FakeResponse(ordem)

    monkeypatch.setattr("app.services.payment_providers.mercado_pago_adapter.requests.request", fake_request)
    provider = MercadoPagoPaymentProvider({
        "MERCADO_PAGO_ACCESS_TOKEN": "token-falso-para-teste",
        "MERCADO_PAGO_SANDBOX": True,
    })
    command = CreatePaymentCommand(
        order_id="17", idempotency_key="pedido-17-pix-v1",
        amount=Decimal("35.50"), method=PaymentMethod.PIX,
        payer_email="cliente@example.com", metadata={{"order_code": "CL-ABC123"}},
    )

    result = provider.create_payment(command)

    assert chamadas[0][0] == "POST"
    assert chamadas[0][1].endswith("/v1/orders")
    assert chamadas[0][2]["headers"]["X-Idempotency-Key"] == "pedido-17-pix-v1"
    payload = chamadas[0][2]["json"]
    assert payload["type"] == "online"
    assert payload["total_amount"] == "35.50"
    assert payload["transactions"]["payments"][0]["payment_method"] == {{"id": "pix", "type": "bank_transfer"}}
    assert payload["payer"]["email"] == "test_payer@example.com"
    assert result.provider_payment_id == "ord:ORD-PIX-17"
    assert result.status is PaymentStatus.PENDING
    assert result.pix_copy_paste == "000201PIX-COPIA-E-COLA-TESTE"
    assert result.pix_qr_code_base64 == "aVZCT1J3MEtHZ29BQUFBTlNVaEVVZ0FBQUFB"
'''
        # The PIX test is the final test in this file in the inspected main branch.
        s = s[:start] + replacement
    changes[rel] = s

    # 9) Replace the standalone outdated legacy-API Pix test with Orders API assertions.
    rel = "backend/tests/business_rules/test_mercadopago_pix.py"
    s = read(root, rel)
    replacement = f'''from decimal import Decimal

from app.services.payment_providers.contracts import (
    CreatePaymentCommand,
    PaymentMethod,
    PaymentStatus,
)
from app.services.payment_providers.mercado_pago_adapter import (
    MercadoPagoPaymentProvider,
)


def test_mercadopago_pix_cria_order_e_retorna_qr_code_sem_redirect():
    provider = MercadoPagoPaymentProvider({{"MERCADO_PAGO_ACCESS_TOKEN": "test-token", "MERCADO_PAGO_SANDBOX": True}})
    calls = []

    def fake_request(method, path, payload=None, params=None, extra_headers=None):
        calls.append((method, path, payload, extra_headers))
        return {pix_order_fixture("42", "35.90", "000201-pix-copia-cola", "aGVsbG8=", "https://www.mercadopago.com.br/ticket/42")}

    provider._request = fake_request
    command = CreatePaymentCommand(
        order_id="42", idempotency_key="order:42:pix:v1", amount=Decimal("35.90"),
        method=PaymentMethod.PIX, payer_email="cliente@example.com", metadata={{"order_code": "CL-42"}},
    )
    result = provider.create_payment(command)

    assert calls[0][0:2] == ("POST", "/v1/orders")
    assert calls[0][2]["type"] == "online"
    assert calls[0][2]["external_reference"] == "42"
    assert calls[0][2]["total_amount"] == "35.90"
    assert calls[0][3]["X-Idempotency-Key"] == "order:42:pix:v1"
    assert result.provider_payment_id == "ord:ORD-PIX-42"
    assert result.status is PaymentStatus.PENDING
    assert result.pix_copy_paste == "000201-pix-copia-cola"
    assert result.pix_qr_code_base64 == "aGVsbG8="
    assert result.approval_url == "https://www.mercadopago.com.br/ticket/42"
'''
    changes[rel] = replacement

    # Write only after every source file passed its expected-content assertions.
    backup = root.parent / f"CandyLand-backup-testfix-{datetime.now():%Y%m%d-%H%M%S}"
    backup.mkdir(parents=True, exist_ok=False)
    changed_files = []
    for rel, content in changes.items():
        path = root / rel
        original = path.read_bytes()
        backup_path = backup / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_bytes(original)
        path.write_text(content, encoding="utf-8", newline="\n")
        changed_files.append(rel)

    print("Arquivos corrigidos:")
    for rel in changed_files:
        print(f"  - {rel}")
    print(f"Backup criado em: {backup}")
    print("Nenhuma regra de produção de pagamento, frete ou autorização foi afrouxada.")
    return changed_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).expanduser().resolve()
    if not (root / ".git").exists() or not (root / "backend").is_dir():
        raise SystemExit(f"Raiz CandyLand inválida: {root}")
    patch(root)


if __name__ == "__main__":
    main()
