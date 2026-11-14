# `com.candyland.mobile.push`

- `CandyLandFirebaseMessagingService.kt`: trata mensagens recebidas do Firebase Cloud Messaging.
- `PushTokenManager.kt`: obtém e envia o token do dispositivo para a API, associado ao usuário autenticado.

O registro do token não comprova entrega de push. Validar envio real, permissões Android, refresh do token, logout e seleção do destinatário.
