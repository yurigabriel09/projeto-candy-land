# Validação das correções — 28/10/2026

## Arquivos substituídos/adicionados

- `frontend/src/pages/RestaurantConfiguration.jsx`: consulta ViaCEP ao digitar CEP, invalida coordenadas quando o endereço muda e descarta resultados de consultas antigas.
- `frontend/src/components/AddressCoordinates.jsx`: mostra mapa quando existem coordenadas válidas.
- `frontend/src/services/restaurantService.js`: usa `VITE_API_URL` e oferece chamada para atualizar status operacional.
- `backend/app/services/restaurant_service.py`: recupera endereço legado sem `address_id`, valida os campos necessários ao criar endereço e mantém o status ABERTO/FECHADO no banco.
- `backend/app/routes/restaurant_routes.py` e `backend/app/controllers/restaurant_controller.py`: rota autenticada de atualização de status operacional.
- `frontend/src/pages/BusinessHome.jsx`: permite ao parceiro abrir/fechar uma loja já liberada e apresenta erros de persistência.
- `frontend/src/services/categoryService.js` e `frontend/src/services/productService.js`: usam `VITE_API_URL`.
- `backend/run.py`: restrição CORS baseada em `FRONTEND_URL` e debug desligado fora de desenvolvimento/testes.
- `backend/.env.example`: URLs locais de retorno e webhooks vazios até configurar o ambiente público HTTPS.
- `backend/tests/business_rules/test_restaurant_configuration.py` e `backend/tests/business_rules/test_restaurant_status.py`: testes de regressão adicionados.

## Resultado da validação disponível nesta sessão

- `python -m py_compile` passou para os arquivos `.py` incluídos no pacote.
- O ZIP foi aberto e validado com `unzip -t` sem erros.
- A suíte completa de pytest e o build do React/Vite não foram executados, pois o clone integral e as dependências do projeto não estão disponíveis neste ambiente. Rode ambos no seu checkout antes de integrar.

## Antes do commit/push

1. Extraia o ZIP na raiz do checkout da branch `feature/paypal-mercadopago-pix`, substituindo os arquivos de mesmo caminho e aceitando os três novos arquivos em `docs/` e os dois novos testes.
2. Confira `git diff` e `git status`.
3. Execute `python -m pytest -q` no backend e `npm ci && npm run build` no frontend.
4. Valide manualmente CEP/endereço, salvar configuração, coordenadas e abertura/fechamento de loja.
5. Commit e push somente depois de os testes locais passarem.

**Segurança:** o pacote não contém o arquivo `backend/.env` real, tokens, credenciais, banco local ou `node_modules`.
