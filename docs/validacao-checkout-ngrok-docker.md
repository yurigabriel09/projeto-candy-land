# Validação do checkout, Mercado Pago, PayPal e Docker

## Segurança antes de testar

O Access Token e o segredo de webhook foram colados em uma conversa. Considere-os expostos e substitua-os no painel do provedor. Use exclusivamente credenciais TEST/Sandbox nesta fase. Não compartilhe `backend/.env`, não o adicione ao Git e não inclua tokens em prints.

## Teste local primeiro (mais fácil de depurar)

1. Abra quatro terminais PowerShell na raiz do projeto.
2. Terminal 1 — backend: `cd backend; python run.py`.
3. Terminal 2 — frontend: antes de iniciar, defina `VITE_API_URL` no arquivo `frontend/.env.local` para a URL HTTPS do túnel do backend. Preserve o `VITE_GOOGLE_CLIENT_ID` já existente. Depois execute `cd frontend; npm run dev -- --host 0.0.0.0`.
4. Terminal 3 — mantenha o túnel do backend ativo: `ngrok http 5000` (ou mantenha o atual se o endereço não mudar).
5. Terminal 4 — túnel do frontend: `ngrok http 5173`. Copie a URL HTTPS mostrada.
6. Defina no terminal onde o Vite será iniciado `NGROK_FRONTEND_HOST` com somente o hostname exato do túnel (sem `https://` e sem caminho). A configuração Vite deste patch aceita somente esse host explícito.
7. No `backend/.env`, configure `FRONTEND_URL`, `MERCADO_PAGO_RETURN_URL_BASE` e `PAYPAL_RETURN_URL_BASE` com a URL HTTPS do frontend; configure `MERCADO_PAGO_NOTIFICATION_URL` com a URL HTTPS do backend mais `/pedidos/webhooks/mercadopago`. Reinicie o backend após alterar o `.env`.
8. Crie um pedido NOVO e uma NOVA tentativa de pagamento: uma preferência já criada no Mercado Pago guarda os `back_urls` antigos.

Exemplo de `frontend/.env.local` (acrescente/atualize somente `VITE_API_URL`; preserve as demais variáveis):

```dotenv
VITE_API_URL=https://URL-HTTPS-DO-BACKEND
```

Exemplo de variáveis do backend, com valores ilustrativos e sem segredos:

```dotenv
FRONTEND_URL=https://URL-HTTPS-DO-FRONTEND
MERCADO_PAGO_RETURN_URL_BASE=https://URL-HTTPS-DO-FRONTEND
PAYPAL_RETURN_URL_BASE=https://URL-HTTPS-DO-FRONTEND
MERCADO_PAGO_NOTIFICATION_URL=https://URL-HTTPS-DO-BACKEND/pedidos/webhooks/mercadopago
```

## Ordem de teste

1. `GET https://URL-HTTPS-DO-BACKEND/restaurantes` deve retornar catálogo público. Confira que as docerias com `ativo=true` aparecem na Home.
2. Entre como cliente, crie um pedido de `PICKUP` para validar pagamento sem bloquear no Google Geocoding.
3. Mercado Pago: escolha Pix para receber QR/Copia e Cola; ou escolha Mercado Pago para abrir Checkout Pro de cartão. Conclua com a conta/cartão de teste do Mercado Pago.
4. Confirme retorno do navegador à rota `/checkout/resultado?order_id=...`, confira a consulta do backend e o estado `PAGAMENTO_CONFIRMADO`; a lista `pagamentos-pendentes` deve deixar de exibir esse pedido e o histórico passa a exibi-lo.
5. PayPal: escolha PayPal, aprove com uma conta Sandbox de comprador e confirme que o backend captura a ordem; o navegador retorna à página de resultado.
6. Recarregue a tela de resultado. O pedido não pode baixar estoque novamente.
7. Abra `/minha-conta/historico-compras`. Para retirada, o restaurante muda o pedido para `PRONTO_PARA_ENTREGA`; o cliente gera um código de seis dígitos no histórico e informa ao restaurante; o restaurante valida o código e o pedido passa a `FINALIZADO`.
8. Geocoding: se a API Google não estiver configurada, use o campo de coordenadas e salve latitude/longitude. Para entrega, use coordenadas reais do endereço, não a localização do computador se ele estiver em outro local.

## Docker depois do teste local

Verifique `docker --version` e `docker compose version`. Pare os processos locais que usam as portas 5000 e 5173 antes de subir os contêineres. Não use `docker compose down -v`, porque `-v` remove o volume nomeado do banco.

Na mesma janela PowerShell em que vai chamar o Compose, configure as variáveis de build:

```powershell
$env:VITE_API_URL = "https://URL-HTTPS-DO-BACKEND"
# Preserve o valor atual do client ID do Google; se o projeto não tiver no ambiente, carregue-o de sua configuração local.
$env:VITE_GOOGLE_CLIENT_ID = "SEU_CLIENT_ID_GOOGLE"
docker compose up --build
```

O compose passa `VITE_API_URL` para o build estático do frontend. Depois que os contêineres estiverem saudáveis, os mesmos túneis apontam para as portas do host: 5000 (backend) e 5173 (frontend). Se `VITE_API_URL` mudar, é necessário reconstruir o frontend com `docker compose up --build`.

## Critérios de sucesso

- O checkout retorna ao frontend HTTPS sem erro de URL.
- Webhooks recebidos são verificados pelo adaptador e consultam o provedor; HTTP 200 sozinho não significa que o pagamento foi aprovado.
- Apenas o estado aprovado pelo provedor confirma o pedido e desconta o estoque uma única vez.
- A compra confirmada aparece no histórico e deixa de aparecer na lista de pendentes.
- O código de recebimento é validado pelo restaurante e não fica armazenado em texto puro.
- A aplicação pode testar entrega usando coordenadas salvas, mesmo sem Google Geocoding.

## Limitações

- Não foi possível realizar compra real no Sandbox a partir do ambiente de preparação desta documentação; os testes do projeto devem ser executados na `.venv` local com suas próprias credenciais de teste.
- O túnel ngrok é temporário no plano gratuito. Se o endereço mudar, atualize `.env`, o `VITE_API_URL`, e reinicie/reconstrua os processos afetados.
