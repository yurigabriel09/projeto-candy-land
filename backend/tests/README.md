# `backend/tests/` — testes automatizados

A suíte é dividida por domínio para deixar claro o risco que cada grupo cobre:

- `authentication/`: códigos, identidade, login de canal único e OAuth.
- `business_rules/`: regras de pedidos, pagamento, estoque, entrega, catálogo, geocoding, restaurantes e adaptadores.
- `checkout/`: endpoints e contrato de checkout.
- `integration/`: fluxos ponta a ponta/smoke de MVP.
- `notifications/`: registro e propriedade de tokens de dispositivo.
- `security/`: autorização e proteção da API.

Para a primeira correção, executar toda a suíte e acrescentar testes de regressão para pedido pendente, criação de tentativa, confirmação de webhook duplicado, pagamento recusado e cancelamento. Relatar comandos e resultados no PR; esta auditoria não executou os testes.
