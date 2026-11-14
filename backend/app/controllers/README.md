# `backend/app/controllers/` — controladores oficiais

Cada arquivo adapta entrada/saída HTTP para os serviços correspondentes:

- `auth_controller.py`: solicita/verifica códigos de autenticação e encaminha autenticação Google/Facebook.
- `category_controller.py`: operações expostas de categorias.
- `order_controller.py`: criação, consulta, atualização, cancelamento e operações de recebimento/entrega de pedidos.
- `payment_controller.py`: criação/consulta de pagamentos, simulação de desenvolvimento, captura/cancelamento PayPal e webhooks dos provedores.
- `product_controller.py`: operações de catálogo/produtos.
- `restaurant_controller.py`: cadastro, configuração, geocoding, estado operacional e produtos do restaurante.
- `user_controller.py`: consulta e atualização de dados do usuário.

As rotas importam estes módulos pelo caminho `app.controllers.*`. A pasta aninhada `controllers/controllers/` era redundante e está sendo removida; não recriar cópias neste local. Controladores devem permanecer finos: validação HTTP e delegação, não regras de estoque/pagamento duplicadas.
