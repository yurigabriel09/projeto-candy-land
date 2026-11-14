# `backend/app/routes/` — endpoints Flask

- `auth_routes.py`: endpoints de código de autenticação e OAuth/deep-link callback.
- `category_routes.py`: endpoints de categorias.
- `device_routes.py`: registro e remoção de tokens de dispositivo autenticado.
- `order_routes.py`: endpoints de pedidos, pagamento, transições de status, webhooks e confirmação de recebimento.
- `product_routes.py`: endpoints de catálogo/produtos.
- `restaurant_routes.py`: cadastro/configuração de restaurante, catálogo, geocoding e operação.
- `user_routes.py`: perfil e operações de usuário.

As rotas definem método HTTP, parâmetros e decorators de autorização; a regra de negócio pertence a services. Os imports ativos apontam para `app.controllers.*`, não para o diretório duplicado que foi removido.
