# Mapa da estrutura do repositório

Este mapa descreve a árvore versionada analisada em 14/11/2026. Pastas de build, cache, ambientes virtuais e dependências locais ignoradas pelo Git não aparecem aqui.

## Raiz do projeto

| Caminho | Responsabilidade |
|---|---|
| `DOCUMENTACAO.md` | Entrada rápida para a documentação técnica. |
| `README.md` | Apresentação geral e instruções históricas do projeto; revisar os trechos de escopo que ficaram desatualizados. |
| `.gitignore` | Define arquivos e diretórios que não devem entrar no Git. |
| `.vscode/settings.json` | Preferências do workspace do VS Code. |
| `docker-compose.yml` | Orquestra os serviços locais conteinerizados. |
| `limpar_e_gerar_zip.cmd` / `.ps1` | Entradas legadas para limpeza e geração de pacote ZIP. |
| `backend/` | API Flask, regras de negócio, persistência e testes de backend. Ver [guia do backend](../../backend/README.md). |
| `frontend/` | Aplicação web React/Vite. Ver [guia do frontend](../../frontend/README.md). |
| `mobile/` | Aplicativo Android nativo Kotlin e configuração Gradle. Ver [guia Android](../../mobile/ARQUITETURA.md). |
| `docs/` | Requisitos, decisões técnicas, relatórios, diagramas e guias de configuração. Ver [guia de documentação](../README.md). |
| `scripts/` | Scripts de preparação do ambiente, ZIP limpo e apoio ao fluxo de PRs. |

## Backend

- `backend/.dockerignore`: exclui arquivos locais do contexto Docker.
- `backend/.env.example`: modelo de variáveis de ambiente; não é arquivo de segredo e deve conter apenas valores de exemplo.
- `backend/Dockerfile`: imagem da API.
- `backend/requirements.txt`: dependências Python.
- `backend/run.py`: cria/configura a aplicação Flask, inicializa extensões, registra blueprints e prepara migrações.
- `backend/app/config/`: configuração por ambiente.
- `backend/app/controllers/`: controladores HTTP que traduzem requisições em chamadas de serviço.
- `backend/app/database/`: conexão ORM e migrações.
- `backend/app/models/`: entidades persistidas.
- `backend/app/routes/`: endpoints e blueprints.
- `backend/app/services/`: regras de negócio e integrações.
- `backend/app/utils/`: autenticação transversal, formatação, data/hora e arquivos.
- `backend/tests/`: testes divididos por domínio.

Documentação específica: [backend/README.md](../../backend/README.md).

## Frontend

- `frontend/package.json` e `package-lock.json`: dependências e versões resolvidas.
- `frontend/vite.config.js`: configuração de desenvolvimento/build.
- `frontend/nginx.conf`: publicação/servidor estático em produção conteinerizada.
- `frontend/src/App.jsx`: composição de rotas e layout principal.
- `frontend/src/pages/`: telas da jornada do cliente e do restaurante.
- `frontend/src/components/`: componentes reutilizáveis.
- `frontend/src/context/`: estado global de autenticação e carrinho.
- `frontend/src/hooks/`: lógica reutilizável associada ao ciclo de vida React.
- `frontend/src/services/`: clientes de API por domínio.
- `frontend/src/utils/`: validadores, máscaras, normalização e notificações.

Documentação específica: [frontend/README.md](../../frontend/README.md).

## Android

- `mobile/build.gradle.kts`, `settings.gradle.kts` e `gradle.properties`: build e configuração do projeto Android.
- `mobile/gradle/`: catálogo de versões, configuração de JVM do Gradle e wrapper.
- `mobile/app/src/main/AndroidManifest.xml`: declaração da aplicação, activity, permissões e serviços.
- `mobile/app/src/main/java/com/candyland/mobile/`: implementação Android atual ligada à API.
- `mobile/app/src/main/java/com/example/candyland/`: pacote legado/protótipo que deve ser avaliado separadamente antes de qualquer exclusão.
- `mobile/app/src/main/res/`: ícones, strings, temas e regras de backup.
- `mobile/app/src/test/` e `androidTest/`: testes unitários e instrumentados.

Documentação específica: [mobile/ARQUITETURA.md](../../mobile/ARQUITETURA.md).

## Docs e scripts

- `docs/Credenciais/`: instruções ilustradas de configuração de fornecedores. Imagens devem ser inspecionadas manualmente para garantir que chaves/tokens estejam ocultos.
- `docs/icone/`: material de identidade visual.
- `scripts/`: automações para Windows; os pares `.cmd` normalmente encaminham para `.ps1`.

## Convenções de manutenção

- Quando uma pasta ganhar um novo arquivo, atualize o README daquela pasta.
- Não documente segredo real. Use nomes de variáveis e valores fictícios.
- Não apague módulos apenas porque parecem antigos: confira imports, rotas, manifest, Gradle e testes.
- Para alterações de fluxo, registre o contrato de API e os critérios de aceite junto com a implementação.
