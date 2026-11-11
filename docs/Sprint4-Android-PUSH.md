# Sprint 4 — Aplicativo Android Kotlin e PUSH

## Entrega técnica

O projeto `mobile/` contém um aplicativo Android nativo em Kotlin + Jetpack Compose. Não é uma rota Flask, PWA ou página React. Ele é aberto separadamente no Android Studio e consome a API HTTP do mesmo backend CandyLand.

O backend recebeu o registro autenticado de dispositivos (`POST/DELETE /devices/fcm`) e o envio FCM HTTP v1. O registro associa um token de aparelho a uma conta PERSONAL ou BUSINESS; não aceita associação sem JWT. A cada transição persistida do pedido ou da entrega, o serviço de pedidos dispara a notificação depois do commit. A indisponibilidade do Firebase não reverte a operação transacional.

## Escopo Android v1

- Login/cadastro de clientes pela verificação já existente em dois canais.
- Catálogo de docerias e produtos.
- Carrinho, pedidos, seleção de retirada/entrega, geocodificação e início do pagamento.
- Histórico de pedidos.
- Registro de token FCM e apresentação de notificações nativas.

O aplicativo v1 não contém painel mobile para contas BUSINESS. O painel web continua sendo a interface de operação das docerias; o suporte do servidor a tokens BUSINESS permite implementar um segundo app/tela posteriormente.

## Configuração necessária antes de usar PUSH real

- Android: `mobile/app/google-services.json` do Firebase project, package `com.candyland.mobile`.
- Backend: conta de serviço Firebase salva como `backend/secrets/firebase-service-account.json` e variáveis `FCM_PROJECT_ID` + `FCM_SERVICE_ACCOUNT_FILE` no `.env`.
- Docker: o compose monta `backend/secrets` em `/app/secrets` em modo somente leitura; a chave não é incorporada à imagem.

Sem estes dois lados configurados, o app continua funcionando para login, catálogo e pedidos, mas nenhum push real será entregue.

## Validação

- Python: validar sintaxe de todos os arquivos `.py` com `python -m compileall -q backend/app backend/tests`.
- Backend: executar `python -m pytest -q` dentro de `backend` com as dependências de `backend/requirements.txt` instaladas.
- Android: abrir `mobile/` no Android Studio, usar JDK 17 + Gradle 8.13, sincronizar e executar testes/build no SDK 36. O build Android não foi executado nesta estação: não há Android SDK/Gradle e a rede DNS para baixar os binários do Gradle Wrapper está indisponível; o ZIP contém as configurações do wrapper, mas não os scripts/JAR executáveis.
- Integração: testar autenticação de dois canais, catálogo, criação de pedido para retirada e entrega, pagamento de sandbox, token FCM registrado e notificação recebida após cada mudança de status.
