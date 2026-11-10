# CandyLand local — um único endpoint HTTPS do ngrok

O endpoint gratuito `stopping-theorize-anyway.ngrok-free.dev` já estava apontando para o Flask na porta 5000. O erro `ERR_NGROK_334` aconteceu porque uma segunda sessão tentou iniciar o mesmo hostname para o Vite na porta 5173.

Para testar checkout/retorno/webhook com um único hostname, o endpoint público deve apontar para o Vite. O `vite.config.js` encaminha os caminhos de API e o webhook para o Flask local.

## Configuração

1. Pare somente a sessão antiga do ngrok com `Ctrl+C` no terminal em que ela está rodando. Não pare Flask nem Vite.
2. No `frontend/.env.local`, configure o mesmo endpoint público como API base:

```dotenv
VITE_API_URL=https://stopping-theorize-anyway.ngrok-free.dev
```

Preserve outras variáveis do arquivo, incluindo `VITE_GOOGLE_CLIENT_ID`. Não compartilhe nem versiona secrets.

3. Inicie o Vite com o hostname público exato:

```powershell
$env:NGROK_FRONTEND_HOST = "stopping-theorize-anyway.ngrok-free.dev"
cd frontend
npm run dev -- --host 0.0.0.0
```

4. Em outro terminal, na raiz do projeto, inicie o único endpoint:

```powershell
.\ngrok.exe http 5173
```

5. Em `backend/.env`, configure ambas as URLs públicas com o mesmo hostname, pois o proxy roteia por caminho:

```dotenv
FRONTEND_URL=https://stopping-theorize-anyway.ngrok-free.dev
MERCADO_PAGO_RETURN_URL_BASE=https://stopping-theorize-anyway.ngrok-free.dev
PAYPAL_RETURN_URL_BASE=https://stopping-theorize-anyway.ngrok-free.dev
MERCADO_PAGO_NOTIFICATION_URL=https://stopping-theorize-anyway.ngrok-free.dev/pedidos/webhooks/mercadopago
```

Reinicie o Flask após alterar seu `.env`. Use os tokens e segredos de teste recém-gerados, nunca credenciais que tenham sido expostas.

## Por que funciona

- `/` e rotas do React são servidas pelo Vite na porta 5173.
- `/auth`, `/users`, `/restaurantes`, `/produtos`, `/categorias`, `/pedidos` e `/uploads` são encaminhados para `http://127.0.0.1:5000`.
- O webhook Mercado Pago em `/pedidos/webhooks/mercadopago` percorre o mesmo proxy até o Flask.

Esse encaminhamento é apenas para desenvolvimento local. Para Docker, deve ser configurado um proxy equivalente no Nginx do frontend, pois `vite.config.js` só controla o servidor de desenvolvimento.
