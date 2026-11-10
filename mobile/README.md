# CandyLand Mobile (Android/Kotlin)

Aplicativo Android nativo, independente do frontend React, mas integrado ao mesmo backend Flask do CandyLand.

## O que já está implementado

- Tela inicial pública: o app abre na Home e só mostra a autenticação quando a pessoa toca em **Entrar**.
- Login por e-mail **ou** celular: na primeira tela, o cliente escolhe apenas um identificador. A API atual mantém a confirmação em dois fatores e solicita o outro contato na etapa seguinte, em vez de exigir os dois campos ao mesmo tempo.
- Login social nativo com Google (Android Credential Manager) e Facebook (OAuth no navegador com retorno seguro por deep link).
- Cadastro de cliente com os dados exigidos pelo backend e endereço principal.
- Listagem de docerias e leitura do catálogo de produtos.
- Carrinho local, escolha de retirada/entrega e criação de pedido.
- Geocodificação do endereço salvo antes de abrir um pedido de entrega, usando a API já existente no backend.
- Início do pagamento por Pix, Mercado Pago ou PayPal, de acordo com os meios configurados no backend.
- Consulta do histórico de pedidos.
- Registro do token FCM associado à conta autenticada e recebimento de notificações Android.
- JWT guardado cifrado com AES-GCM e chave protegida pelo Android Keystore.

A primeira versão do aplicativo é para **clientes (PERSONAL)**. Contas de doceria (BUSINESS) continuam usando o painel web existente; o backend aceita tokens FCM de ambos os tipos para permitir a futura versão mobile de parceiros.

## Abrir no Android Studio

1. Extraia o pacote/clone o repositório CandyLand.
2. No Android Studio, escolha **Open** e selecione a pasta `mobile` (não selecione `frontend` nem `backend`).
3. Instale o Android SDK 36 e um JDK 17 quando o Android Studio solicitar.
4. Configure o Gradle JDK como **JDK 17** e a distribuição **Gradle 8.13**. O pacote inclui `gradle-wrapper.properties`, mas esta estação de preparação não tinha Gradle/SDK nem acesso de rede para baixar os binários da Wrapper (`gradlew`, `gradlew.bat` e `gradle-wrapper.jar`). Se o Android Studio indicar que o wrapper está ausente, use uma instalação local do Gradle 8.13 ou gere os arquivos da Wrapper em um ambiente com Gradle 8.13 instalado, executando `gradle wrapper --gradle-version 8.13` dentro de `mobile`.
5. Aguarde a sincronização dos plugins e dependências Gradle.
6. Crie/edite `mobile/local.properties` (preserve a linha `sdk.dir` que o Android Studio criar) e adicione a URL do backend:

```properties
CANDYLAND_API_BASE_URL=http://10.0.2.2:5000/
# Mesmo OAuth Web Client ID configurado como GOOGLE_CLIENT_ID no backend.
CANDYLAND_GOOGLE_WEB_CLIENT_ID=SEU_CLIENT_ID_WEB.apps.googleusercontent.com
```

`10.0.2.2` é o endereço especial que faz o emulador Android acessar a máquina host. Para um celular físico, substitua pelo IP local do computador na rede Wi-Fi, por exemplo `http://192.168.0.15:5000/`. O aparelho e o computador precisam estar na mesma rede e o firewall do Windows deve permitir a porta 5000.

## Subir o backend para desenvolvimento

Em outro terminal, na pasta `backend`:

```powershell
..\.venv\Scripts\python.exe run.py
```

O Flask já escuta em `0.0.0.0:5000` nos ambientes de desenvolvimento, permitindo o acesso pelo emulador/rede local. Confirme que `GET http://localhost:5000/restaurantes` responde no computador antes de abrir o app.

O app Android nativo não está sujeito à política CORS do navegador. Ainda assim, ele usa exatamente as mesmas rotas e regras de autorização do backend web.

## Login Google e Facebook

### Google

1. Crie um OAuth Client ID do tipo **Web application** no Google Cloud. O backend valida o ID token com esse client ID.
2. Configure o mesmo valor em `GOOGLE_CLIENT_ID` no `backend/.env` e em `CANDYLAND_GOOGLE_WEB_CLIENT_ID` no `mobile/local.properties`.
3. Cadastre também um OAuth Client ID Android para o pacote `com.candyland.mobile` e a impressão SHA-1 da chave usada pelo build. Para consultar a SHA-1 de desenvolvimento, execute `gradlew signingReport` no módulo `mobile`.
4. No emulador, entre com uma conta Google em Settings antes de testar o botão.

### Facebook

1. Configure `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET` e `FACEBOOK_REDIRECT_URI` no `backend/.env`. O redirect URI do backend precisa estar cadastrado exatamente no painel Meta/Facebook Login.
2. Configure `FACEBOOK_MOBILE_REDIRECT_URI=com.candyland.mobile://oauth/facebook`. O backend valida o `state`, emite um ticket temporário assinado e só então redireciona de volta ao aplicativo.
3. Para desenvolvimento local com Facebook, use uma URL HTTPS pública (por exemplo, um túnel ngrok) como `CANDYLAND_API_BASE_URL` no `mobile/local.properties` **e** como host de `FACEBOOK_REDIRECT_URI`. Isso garante que o navegador e o callback usem o mesmo host e os cookies de `state` sejam preservados. Não use `localhost` como callback dentro do navegador do emulador.

Os botões ficam visíveis mesmo antes de configurar as credenciais; o login só será concluído quando os respectivos Client IDs e segredos estiverem configurados no ambiente. Não coloque segredos no app Android nem no Git.

## Firebase Cloud Messaging (PUSH)

O código do app e o backend estão preparados para FCM HTTP v1, mas as credenciais de cada projeto são próprias e **não são incluídas no ZIP/Git**.

### Android

1. Crie/abra o projeto no Firebase Console.
2. Adicione um aplicativo Android com o package name `com.candyland.mobile`.
3. Baixe `google-services.json` e coloque em `mobile/app/google-services.json`.
4. Faça Sync Gradle e execute o app em Android 13+; conceda a permissão de notificações quando solicitada.

O `google-services.json` é ignorado pelo Git e não deve ser enviado neste repositório.

### Backend

1. No mesmo projeto Firebase, habilite Firebase Cloud Messaging e crie uma chave/conta de serviço com permissão para enviar mensagens FCM.
2. Salve o JSON no caminho `backend/secrets/firebase-service-account.json`.
3. Configure no `backend/.env`:

```env
FCM_PROJECT_ID=SEU_PROJECT_ID_FIREBASE
FCM_SERVICE_ACCOUNT_FILE=secrets/firebase-service-account.json
```

4. Reinicie o backend. Se usar Docker Compose, a pasta `backend/secrets` é montada como `/app/secrets` somente leitura; crie a pasta/arquivo antes de subir os serviços.

O token do aparelho é registrado em `POST /devices/fcm` com o JWT do cliente. O backend envia as notificações somente depois de confirmar no banco a mudança de status do pedido/entrega. Ausência de credenciais FCM não impede login, catálogo ou checkout; apenas desativa o envio push. Falhas do Firebase não desfazem pedidos já gravados.

## Fluxo conectado ao backend

| Ação no Android | Endpoint Flask existente |
|---|---|
| Login Google | `POST /auth/google` |
| Iniciar OAuth Facebook | `GET /auth/facebook?platform=ANDROID` |
| Concluir OAuth Facebook | `POST /auth/facebook/complete` |
| Solicitar primeiro código | `POST /auth/login` |
| Solicitar segundo código | `POST /auth/second-code` |
| Validar código | `POST /auth/verify` |
| Criar conta de cliente | `POST /users` |
| Listar docerias | `GET /restaurantes` |
| Consultar produtos da doceria | `GET /restaurantes/{id}/produtos` |
| Listar endereços do cliente | `GET /users/{id}/enderecos` |
| Geocodificar endereço | `POST /users/{id}/enderecos/{endereco_id}/geocodificar` |
| Criar pedido | `POST /pedidos` |
| Iniciar pagamento | `POST /pedidos/{id}/pagamento` |
| Consultar pedidos | `GET /pedidos` |
| Registrar/remover token FCM | `POST/DELETE /devices/fcm` |

As rotas de pedidos/endereço/token protegido usam `Authorization: Bearer <JWT>`; o interceptor Retrofit injeta o token da sessão automaticamente.

## Observações de produção

- Configure `CANDYLAND_API_BASE_URL` com URL HTTPS pública do backend. HTTP sem TLS só é habilitado no build `debug` para desenvolvimento local; o build `release` bloqueia cleartext.
- Configure assinatura de release, política de privacidade e ícones definitivos antes de publicar na Play Store.
- O checkout depende dos provedores de pagamento configurados no backend. O app abre o `approval_url` no navegador quando o provedor exige aprovação externa e mostra o Pix copia-e-cola quando retornado.
- O app consulta o histórico ao abrir/atualizar a aba Pedidos; as notificações push são uma camada adicional, não substituem a consulta autenticada ao backend.
