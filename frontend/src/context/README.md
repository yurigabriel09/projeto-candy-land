# `frontend/src/context/`

- `AuthContext.jsx`: estado global de autenticação, usuário/perfil e sessão.
- `CartContext.jsx`: estado do carrinho, itens, quantidades, tipo de pedido e persistência local.

Mudanças no carrinho devem preservar consistência entre UI e payload enviado ao backend. O carrinho não é fonte confiável de preço ou estoque; revalidar no servidor.
