# OAuth Google e Facebook — configuração e validação

**Estado:** testes de serviço/rotas usam respostas simuladas. O login com credenciais reais ainda precisa ser verificado na máquina/conta de desenvolvedor da equipe. Nunca copie segredos para commits, logs ou capturas de tela.

## 1. Configuração local

Use `backend/.env.example` e `frontend/.env.example` como referência; crie/edite os `.env` locais sem versioná-los. Para o fluxo Facebook, mantenha o hostname idêntico nos pontos abaixo. A configuração de exemplo usa `localhost` em todos eles, não misture com `127.0.0.1`.

No `frontend/.env`:

```dotenv
VITE_API_URL=http://localhost:5000
VITE_GOOGLE_CLIENT_ID=SEU_CLIENT_ID_WEB.apps.googleusercontent.com
```

No `backend/.env`:

```dotenv
FRONTEND_URL=http://localhost:5173
GOOGLE_CLIENT_ID=SEU_CLIENT_ID_WEB.apps.googleusercontent.com
GOOGLE_CLOCK_SKEW_SECONDS=300
FACEBOOK_CLIENT_ID=ID_DO_APP_META
FACEBOOK_CLIENT_SECRET=SEGREDO_DO_APP_META
FACEBOOK_REDIRECT_URI=http://localhost:5000/auth/facebook/callback
APP_ENV=development
SECRET_KEY=UMA_CHAVE_LOCAL_FORTE_E_ALEATORIA
```

`GOOGLE_CLIENT_ID` e `VITE_GOOGLE_CLIENT_ID` precisam ser o mesmo Client ID de tipo **Web application**. O ID é público; `FACEBOOK_CLIENT_SECRET` e `SECRET_KEY` são segredos e ficam apenas no backend. Após alterar variáveis `VITE_*`, reinicie o servidor Vite. Após alterar `.env` do backend, reinicie o Flask.

## 2. Google Cloud

1. Crie/selecione um OAuth Client ID do tipo Web application.
2. Em **Authorized JavaScript origins**, cadastre a origem usada no navegador, por exemplo `http://localhost:5173`. A origem inclui protocolo e porta e não inclui `/login`. Se usar uma origem diferente, cadastre-a explicitamente.
3. Configure branding/consentimento e teste com usuários permitidos pelo estado de publicação do app.
4. Copie o mesmo Client ID para `VITE_GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_ID`.
5. No login, confirme que o backend rejeita token inválido/audience incorreta e e-mail não verificado. A verificação de assinatura, expiração, emissor e audience é feita por `google-auth`; não aceite a resposta do frontend como prova de identidade.

Referência oficial: [Google Identity Services — configurar o Client ID](https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid).

## 3. Meta/Facebook Login

1. Configure um app Meta com o produto Facebook Login para Web e credenciais próprias de cada ambiente.
2. Cadastre exatamente `http://localhost:5000/auth/facebook/callback` em **Valid OAuth Redirect URIs** no ambiente local. Protocolo, hostname, porta e caminho precisam coincidir com `FACEBOOK_REDIRECT_URI`. Para homologação/produção, use a URL HTTPS real do backend e cadastre o valor exato.
3. Mantenha os escopos do fluxo limitados a `email` e `public_profile`; teste em modo de desenvolvimento com uma conta autorizada.
4. Confirme que `VITE_API_URL` e `FACEBOOK_REDIRECT_URI` usam o mesmo hostname para que o cookie de `state` seja enviado no callback.
5. O endpoint `/auth/facebook` cria `state` aleatório, envia-o ao provedor e grava o mesmo valor em cookie HttpOnly, `SameSite=Lax`, com validade de cinco minutos. O cookie recebe `Secure` em produção. O callback só processa `code` se `state` corresponder; sucesso, cancelamento ou falha limpam os cookies.
6. O botão envia o contexto `PERSONAL` ou `BUSINESS` para que o callback volte à rota de login correta (`/login` ou `/parceiros/login`).
7. O ticket assinado que volta ao frontend expira em cinco minutos. Não o registre em logs nem o compartilhe.

## 4. Testes automatizados

Na raiz do repositório, dentro do ambiente virtual já preparado:

```powershell
cd backend
python.exe -m pytest tests\authentication\test_oauth_providers.py -q
python.exe -m pytest -q
cd ..\frontend
npm run build
cd ..
git diff --check
```

Os testes substituem as respostas dos provedores por dados simulados e verificam validação do token Google, normalização de e-mail, ausência de logs sensíveis, URL/`state` do Facebook, emissão/verificação de ticket, callback, cancelamento, cookies `Secure` em produção, retorno para PERSONAL/BUSINESS e recusa de `state` inválido. **Eles não comprovam que as credenciais reais estão corretas ou que as contas do painel externo estão configuradas.**

## 5. Roteiro manual com provedor real

- [ ] Reiniciar frontend e backend após conferir as variáveis locais.
- [ ] Entrar pelo botão Google e confirmar que uma conta existente chega à área correta (`/home` para PERSONAL e `/business` para BUSINESS).
- [ ] Testar Google com credencial inválida/audience errada; a API deve recusar sem imprimir token, claims ou e-mail nos logs.
- [ ] Entrar pelo Facebook, aprovar permissões e confirmar que o callback volta à tela de login e conclui a autenticação.
- [ ] Cancelar no provedor; conferir mensagem amigável e nenhuma sessão iniciada.
- [ ] Tentar callback com `state` ausente/diferente; deve ser recusado sem trocar o código por token.
- [ ] Validar o caminho de conta sem e-mail/celular conforme as regras de cadastro e manter o e-mail globalmente único.
- [ ] Repetir os fluxos no ambiente de homologação HTTPS usando credenciais separadas das locais.
- [ ] Conferir que nenhum segredo ou token aparece no Git, logs, URL compartilhada ou evidência anexada ao PR.

## 6. Verificação do fluxo de parceiros e da sessão

- [ ] Na página inicial, clicar em **Saiba mais** abre `/parceiros`; **Seja um parceiro você também!** abre `/parceiros/login`.
- [ ] A landing `/parceiros` está formatada e oferece entrada/cadastro sem exigir uma sessão prévia.
- [ ] Em `/parceiros/login`, aparecem as opções de e-mail/celular, Google e Facebook.
- [ ] Um novo cadastro iniciado por Google ou Facebook, depois da verificação de celular, segue para `/register/business`; o login por e-mail/celular segue a mesma regra.
- [ ] Uma conta BUSINESS existente entra em `/business`; uma conta PERSONAL existente continua sendo direcionada à sua área pessoal, mesmo que inicie o login pela página de parceiros.
- [ ] `/parceiros` e `/parceiros/login` são públicos intencionalmente; as páginas operacionais `/business` e suas rotas filhas continuam protegidas por `ProtectedRoute` para o tipo `BUSINESS`.
- [ ] Respostas dos endpoints `/auth/*` retornam `Cache-Control: no-store` e `Pragma: no-cache`.
- [ ] Não há `console.log` imprimindo a resposta completa dos cadastros, pois ela contém o token de sessão.

O token JWT continuar visível no corpo da resposta de login, inclusive na aba Network do navegador que está autenticando, é esperado no desenho atual de autenticação por bearer token. O frontend precisa receber o token para criar a sessão. Não se deve compartilhar essa resposta, salvar o token em logs ou capturas de tela. Esconder o token do DevTools sem mudar a arquitetura não é possível; usar cookie `HttpOnly` exigiria uma migração do transporte da sessão e proteção contra CSRF.

## 7. Critério de conclusão

OAuth só pode ser marcado como validado depois de: testes automatizados aprovados; login real com cada provedor; conta existente roteada corretamente; cancelamento e falhas tratados; configuração de homologação testada; e evidências sem dados sensíveis anexadas à entrega. A suíte com mocks, isoladamente, não atende esse critério.
