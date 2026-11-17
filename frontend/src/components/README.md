# `frontend/src/components/`

- `AddressCoordinates.jsx`: formulário/visualização de endereço e coordenadas.
- `DashboardSidebar.jsx`: navegação lateral do painel do restaurante.
- `Header.jsx`: cabeçalho e navegação global.
- `LocationMap.jsx`: exibição de mapa/localização.
- `PixPayment.jsx`: QR Code e dados de pagamento Pix.
- `ProductRecommendations.jsx`: recomendações de produtos.
- `ProtectedRoute.jsx`: protege rotas que exigem autenticação/perfil.
- `RegistrationGuard.jsx`: protege e organiza etapas de cadastro.
- `VerifiedPhoneInput.jsx`: exibe o telefone confirmado durante o cadastro.

O componente antigo `PhoneInput.jsx` foi removido porque não tinha importadores; os formulários atuais usam `VerifiedPhoneInput.jsx`.
