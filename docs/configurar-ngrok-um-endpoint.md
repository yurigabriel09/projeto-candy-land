# CandyLand — um único endpoint HTTPS do ngrok

O navegador deve acessar o frontend pelo hostname público do ngrok. As chamadas da API usam caminhos relativos (`/auth`, `/users`, `/restaurantes`, `/pedidos` e `/uploads`) e são encaminhadas ao Flask pelo proxy da mesma origem.

Assim, não configuramos o browser para chamar `localhost:5000` ou outro hostname ngrok diretamente. Isso evita CORS e também permite que o mesmo hostname seja usado no Android e nos callbacks OAuth.

## Opção A — frontend Vite local + Flask local

1. Inicie o Flask na porta 5000, escutando em `0.0.0.0`.
2. No `frontend/.env.local`, deixe a URL da API vazia:

```dotenv
VITE_API_URL=
```

Preserve outras variáveis, como `VITE_GOOGLE_CLIENT_ID`. Não coloque credenciais no frontend.

3. Inicie o Vite na porta 5173:

```powershell
cd frontend
npm run dev -- --host 0.0.0.0
```

4. Em outro terminal, inicie apenas um túnel apontando para o Vite:

```powershell
ngrok http 5173
```

Acesse `https://SEU_HOST_NGROK/login`. O Vite encaminha os caminhos da API para `http://127.0.0.1:5000` usando `frontend/vite.config.js`.

## Opção B — Docker Compose

1. Confirme que `backend/.env` contém as variáveis necessárias, incluindo `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, `FRONTEND_URL` e as URLs de callback dos provedores.
2. Deixe `VITE_API_URL` vazio no ambiente usado pelo Docker Compose. O padrão do `docker-compose.yml` já é vazio.
3. Reconstrua os containers para atualizar o bundle e o Nginx:

```powershell
docker compose down
docker compose up --build -d
docker compose ps
```

4. Inicie o ngrok para a porta 5173 do host:

```powershell
ngrok http 5173
```

O Nginx do frontend encaminha `/auth`, `/users`, `/restaurantes`, `/produtos`, `/categorias`, `/pedidos` e `/uploads` para `http://backend:5000` na rede interna do Compose. O browser continua na mesma origem HTTPS do ngrok.

## Variáveis do backend para ambiente público

Use o hostname HTTPS público, sem adicionar uma segunda porta ou host diferente:

```dotenv
FRONTEND_URL=https://SEU_HOST_NGROK
FACEBOOK_REDIRECT_URI=https://SEU_HOST_NGROK/auth/facebook/callback
MERCADO_PAGO_RETURN_URL_BASE=https://SEU_HOST_NGROK
PAYPAL_RETURN_URL_BASE=https://SEU_HOST_NGROK
MERCADO_PAGO_NOTIFICATION_URL=https://SEU_HOST_NGROK/pedidos/webhooks/mercadopago
```

Cadastre exatamente a URL de callback do Facebook no painel Meta. Para ambiente local sem túnel, pode usar `http://localhost:5173` como callback, pois o Vite faz proxy de `/auth/facebook/callback` para o Flask. Reinicie o Flask após alterar `backend/.env` e reinicie/reconstrua o frontend após alterar variáveis `VITE_*`.

## Android

O Android nativo não sofre bloqueio CORS. Para o emulador Android, use `CANDYLAND_API_BASE_URL=http://10.0.2.2:5000/` em `mobile/local.properties`. Para um aparelho físico ou teste através do ngrok, use:

```properties
CANDYLAND_API_BASE_URL=https://SEU_HOST_NGROK/
```

Recompile/reinstale o app após alterar `mobile/local.properties`. A rota da API passará pelo mesmo Nginx/Vite proxy, chegando ao Flask.

## Verificação

- `https://SEU_HOST_NGROK/` deve abrir o frontend.
- `https://SEU_HOST_NGROK/restaurantes` deve retornar JSON do Flask, não o HTML do React.
- `https://SEU_HOST_NGROK/auth/login` aceita POST; não teste pelo endereço digitando no navegador.
- Em DevTools > Network, as chamadas do frontend devem usar o mesmo hostname da página, sem chamadas diretas para `localhost:5000`.

Se a página abrir mas `/restaurantes` devolver HTML, o proxy não está encaminhando a rota. Se `/restaurantes` devolver JSON mas ocorrer CORS no browser, algum frontend ainda está usando uma URL absoluta para a API ou o request está indo para um backend externo fora do proxy.
