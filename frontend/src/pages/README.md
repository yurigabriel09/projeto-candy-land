# `frontend/src/pages/` — telas

## Área do restaurante

- `BusinessFinance.jsx`: visão financeira do estabelecimento.
- `BusinessHome.jsx`: início/dashboard do restaurante.
- `BusinessOrders.jsx`: lista e gestão de pedidos recebidos.
- `BusinessRegister.jsx`: cadastro de estabelecimento.
- `BusinessReviews.jsx`: tela de avaliações; no retrato auditado é placeholder porque não há persistência/API completa de reviews.
- `CategoryManager.jsx`: gerenciamento de categorias.
- `ProductForm.jsx`: criação/edição de produto.
- `RestaurantConfiguration.jsx`: configuração do restaurante, endereço, localização e parâmetros operacionais.
- `Cardapio.jsx`: tela/visão de cardápio do estabelecimento.

## Área do cliente e jornada de compra

- `Home.jsx`: tela inicial autenticada/área principal.
- `Landing.jsx`: landing pública.
- `PartnerLanding.jsx`: apresentação para parceiros/restaurantes.
- `Itens.jsx`: listagem de itens/produtos disponível na rota `/itens`.
- `Restaurant.jsx`: detalhe do restaurante e catálogo.
- `Cart.jsx`: revisão do carrinho e tipo de pedido.
- `Checkout.jsx`: coleta de dados e inicialização do pedido/pagamento; foco principal da primeira correção.
- `CheckoutResult.jsx`: retorno/resultado de tentativa de pagamento e acompanhamento de captura/estado.
- `PendingPayments.jsx`: lista/retomada de pagamentos pendentes.
- `PurchaseHistory.jsx`: histórico de compras do cliente.
- `OrderTracking.jsx`: acompanhamento do pedido e mapa/status.

## Conta e cadastro

- `Login.jsx`: autenticação da aplicação web.
- `Register.jsx`: seleção/fluxo de cadastro.
- `PersonalRegister.jsx`: cadastro de cliente.
- `DadosPessoais.jsx`: consulta/edição de dados pessoais.

Ao alterar uma jornada, manter sincronizadas rotas de App.jsx, services, contratos backend e testes. Pagamento só deve ser exibido como confirmado após confirmação validada do servidor.
