# Aplicativo Android — arquitetura e arquivos

O módulo `mobile/` contém o aplicativo Android nativo em Kotlin/Jetpack Compose, separado do frontend web e conectado à API Flask.

## Arquivos da raiz `mobile/`

- `.gitignore`: exclusões específicas do projeto Android.
- `README.md`: instruções de configuração do aplicativo, autenticação, API e integrações externas.
- `build.gradle.kts`: configuração Gradle do projeto raiz.
- `gradle.properties`: propriedades globais de build/Gradle.
- `gradlew` e `gradlew.bat`: wrappers para executar Gradle em Unix/Windows.
- `settings.gradle.kts`: módulos e repositórios Gradle.

## `mobile/app/`

- `.gitignore`: exclusões locais do módulo.
- `build.gradle.kts`: plugins, dependências, SDK e configurações do app.
- `src/main/AndroidManifest.xml`: declara package/Activity, permissões e serviço de mensagens.
- `src/main/keepRules/rules.keep`: regras de preservação para otimização/obfuscation.
- `src/main/res/`: ícones, cores, strings, temas e regras de backup.

## Implementação atual — pacote `com.candyland.mobile`

- `MainActivity.kt`: Activity de entrada do app.
- `data/CandyLandApi.kt`: comunicação HTTP com backend e serialização de endpoints.
- `data/SessionManager.kt`: armazenamento/recuperação da sessão do usuário.
- `model/ApiModels.kt`: modelos Kotlin dos payloads/retornos da API.
- `push/CandyLandFirebaseMessagingService.kt`: recebe mensagens FCM no dispositivo.
- `push/PushTokenManager.kt`: registra/atualiza token FCM na API autenticada.
- `ui/CandyLandApp.kt`: composição de telas e fluxos do usuário (welcome/login, OAuth, catálogo, carrinho, checkout, pedidos e perfil).

## Pacote legado — `com.example.candyland`

Este pacote contém código de protótipo/demo que coexiste com o pacote atual:

- `MainActivity.kt`, `navigation/CandylandApp.kt`: entrada e navegação antigas.
- `data/FakeData.kt`, `data/Models.kt`: modelos e dados simulados.
- `ui/CartViewModel.kt`: estado de carrinho do protótipo.
- `ui/cart/CartScreen.kt`, `ui/checkout/CheckoutScreen.kt`, `ui/checkout/PaymentMethodsSection.kt`, `ui/components/Components.kt`, `ui/home/HomeScreen.kt`, `ui/profile/ProfileScreen.kt`: telas e componentes do protótipo.
- `ui/theme/Color.kt`, `Theme.kt`, `Type.kt`: tema visual antigo.

**Não remover o pacote legado automaticamente.** Antes, confirmar `AndroidManifest.xml`, referências de build/teste e imports. A limpeza dele é tarefa separada da pasta de controladores duplicada do backend.

## Testes e Gradle

- `src/test/java/com/example/candyland/ExampleUnitTest.kt`: teste unitário de exemplo do pacote legado.
- `src/androidTest/java/com/example/candyland/ExampleInstrumentedTest.kt`: teste instrumentado de exemplo do pacote legado.
- `gradle/libs.versions.toml`: catálogo de versões de plugins/dependências.
- `gradle/gradle-daemon-jvm.properties`: configuração do JVM do daemon Gradle.
- `gradle/wrapper/gradle-wrapper.jar` e `gradle-wrapper.properties`: wrapper e versão/distribuição do Gradle.

Arquivos de recursos versionados: `drawable/ic_launcher_background.xml` e `drawable/ic_launcher_foreground.xml` compõem o ícone; `mipmap-anydpi-v26/ic_launcher.xml` e `ic_launcher_round.xml` definem os ícones adaptativos; cada uma das pastas `mipmap-hdpi/`, `mipmap-mdpi/`, `mipmap-xhdpi/`, `mipmap-xxhdpi/` e `mipmap-xxxhdpi/` contém `ic_launcher.webp` e `ic_launcher_round.webp`; `values/colors.xml`, `strings.xml`, `styles.xml` e `themes.xml` definem cores, textos e temas; `xml/backup_rules.xml` e `data_extraction_rules.xml` definem regras de backup/extração de dados. O README de configuração deve ser seguido para client IDs, `google-services.json`, FCM e URL da API.

## Pontos de validação antes de release

1. Build e testes com JDK compatível com a versão do wrapper/Android Gradle Plugin.
2. API base URL para emulador e dispositivo físico.
3. Login email/telefone e Google/Facebook com credenciais reais.
4. Deep link de OAuth e retorno ao aplicativo.
5. Pedido pendente e início de pagamento com o mesmo contrato do frontend web.
6. FCM em aparelho real com token autenticado e notificação após transição válida.
