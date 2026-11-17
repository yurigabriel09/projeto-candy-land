# `backend/app/services/` — serviços de domínio

- `account_identity_service.py`: normalização/resolução de identidade por email e telefone e regras de unicidade.
- `auth_service.py`: fluxo de autenticação, códigos, vínculo de conta e credenciais OAuth.
- `category_service.py`: regras de categoria.
- `device_token_service.py`: cadastro, validação, propriedade e remoção de tokens de dispositivo.
- `email_service.py`: envio de emails transacionais/autenticação.
- `facebook_auth_service.py`: validação do ticket/credencial Facebook e dados de identidade.
- `google_auth_service.py`: validação da credencial Google.
- `order_receipt_service.py`: emissão e validação do código de recebimento do pedido.
- `order_service.py`: criação/consulta/cancelamento, itens, taxa de entrega, estoque e transições principais do pedido. É um ponto crítico para a primeira correção.
- `order_workflow_service.py`: regras/validação das transições do fluxo de pedido.
- `payment_service.py`: orquestra tentativas, provedores, consulta, webhooks, idempotência e confirmação.
- `product_service.py`: catálogo, produtos e disponibilidade.
- `push_notification_service.py`: envio FCM para dispositivos Android.
- `push_service.py`: Web Push para inscrições de navegador.
- `restaurant_service.py`: cadastro, configuração e operações do restaurante.
- `token_service.py`: emissão/validação de tokens da aplicação.
- `user_service.py`: operações do usuário.
- `whatsapp_service.py`: integração de mensagens WhatsApp via fornecedor configurado.
- `payment_providers/`: contratos e adaptadores de provedores. Ver [guia dos provedores](payment_providers/README.md).

Priorize idempotência e transações em pagamento/estoque; registre falhas de integrações e não confirme operação apenas por retorno do cliente.
