# `payment_providers/` — adaptadores de pagamento

- `__init__.py`: inicialização do pacote.
- `contracts.py`: contrato comum esperado dos provedores.
- `factory.py`: seleciona o adaptador conforme configuração/método.
- `mercado_pago_adapter.py`: integração Mercado Pago, incluindo fluxos de pagamento compatíveis com Pix.
- `mock_adapter.py`: provedor simulado para testes/desenvolvimento; nunca representa cobrança real.
- `paypal_adapter.py`: integração PayPal para criação/captura/consulta e recursos associados.

O `PaymentService` deve orquestrar os adaptadores e manter o contrato uniforme. Nunca confiar apenas no redirect do browser: validar status com o provedor e processar webhooks de forma autenticada/idempotente. Credenciais ficam no ambiente, não no código.
