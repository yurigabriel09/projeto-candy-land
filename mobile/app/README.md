# `mobile/app/`

- `.gitignore`: regras locais de exclusão do módulo Android.
- `build.gradle.kts`: configuração do módulo Android, variantes, SDK, plugins e bibliotecas.
- `src/main/`: código e recursos empacotados no aplicativo.
- `src/test/`: testes executados na JVM local.
- `src/androidTest/`: testes instrumentados executados em emulador/aparelho.

O package ativo apontado pela configuração atual deve ser confirmado no Manifest antes de reorganizar os arquivos. O módulo contém tanto o pacote atual `com.candyland.mobile` quanto um protótipo antigo em `com.example.candyland`.
