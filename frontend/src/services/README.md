# `frontend/src/services/` — clientes de API

- `addressService.js`: operações de endereço/geocoding.
- `authService.js`: login, cadastro, autenticação por códigos e OAuth.
- `categoryService.js`: chamadas de categorias.
- `orderService.js`: criação, consulta, status e operações de pedidos/pagamento conforme contrato da API.
- `productService.js`: catálogo e produtos.
- `restaurantService.js`: cadastro, configuração, catálogo e operações de restaurante.
- `userService.js`: perfil e dados do usuário.

A camada de serviço deve centralizar base URL, headers, tratamento de erro e parsing. Não duplicar em componentes chamadas diretas com contratos divergentes.
