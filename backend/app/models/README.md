# `backend/app/models/` — entidades persistidas

- `__init__.py`: agrega/importa modelos para facilitar inicialização do ORM.
- `address.py`: endereço e informações geográficas/endereço vinculadas ao domínio.
- `auth_attempt.py`: tentativa/estado temporário de autenticação.
- `auth_code.py`: códigos de verificação de autenticação.
- `card.py`: dados/token ou referência de cartão conforme o contrato atual; não deve guardar CVV nem número sensível sem tokenização e conformidade apropriadas.
- `category.py`: categoria de catálogo.
- `delivery.py`: dados da entrega vinculada ao pedido.
- `device_token.py`: tokens de dispositivos móveis para push.
- `item_order.py`: itens/quantidades associados a um pedido.
- `order.py`: entidade principal do pedido, status, valores e vínculo com cliente/restaurante.
- `order_receipt_code.py`: código usado para validar recebimento/retirada.
- `payment_attempt.py`: tentativa de pagamento, referência do provedor, status e idempotência.
- `product.py`: produto, preço, disponibilidade e estoque.
- `push_subscription.py`: inscrição de Web Push do navegador.
- `restaurant.py`: restaurante, endereço, configuração e parâmetros comerciais.
- `user.py`: usuários e dados de perfil/autenticação.

Ao adicionar entidades, defina relacionamentos, índices/constraints, cascatas, política de exclusão e migração. Status financeiros devem ser estados explícitos e não inferidos pelo frontend.
