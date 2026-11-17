# `com.candyland.mobile` — pacote Android atual

- `MainActivity.kt`: ponto de entrada da UI Android.
- `data/`: cliente de API e sessão. `CandyLandApi.kt` encapsula chamadas ao backend; `SessionManager.kt` persiste credenciais/dados de sessão.
- `model/`: `ApiModels.kt` define DTOs Kotlin para requisições/respostas.
- `push/`: `CandyLandFirebaseMessagingService.kt` recebe FCM e `PushTokenManager.kt` registra token junto ao backend.
- `ui/`: `CandyLandApp.kt` contém composição e navegação das telas da aplicação.

Este é o pacote de referência para evolução da aplicação mobile atual. Não misturar com modelos fake e telas antigas de `com.example.candyland`.
