# `com.candyland.mobile.data`

- `CandyLandApi.kt`: cliente HTTP/serialização e operações que conectam o app aos endpoints Flask.
- `SessionManager.kt`: gerenciamento local da sessão/autenticação usada nas chamadas protegidas.

Novos endpoints devem ser adicionados aqui com tratamento consistente de HTTP, erro, timeout e autenticação. Não duplicar URL/contrato em cada composable.
