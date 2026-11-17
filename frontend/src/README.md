# `frontend/src/services/` — clientes de API

- `addressService.js`: operações de endereço/geocoding.
- `categoryService.js`: chamadas de categorias.
- `orderService.js`: criação, consulta, status e operações de pedidos/pagamento conforme contrato da API.
- `productService.js`: catálogo e produtos.
- `recommendationService.js`: consulta à API de recomendação.
- `restaurantService.js`: cadastro, configuração, catálogo e operações de restaurante.
- `userService.js`: perfil e dados do usuário.

A autenticação é centralizada em `AuthContext.jsx` e nas rotas/handlers da tela `Login.jsx`; o antigo `authService.js` não tinha importadores e foi removido.
