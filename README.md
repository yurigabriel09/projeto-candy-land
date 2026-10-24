# CandyLand — guia do projeto e estado real

> **Atualizado em 11/10/2026.** Este README é a fonte de orientação do repositório. Os percentuais são uma estimativa de entrega por funcionalidade baseada no código e na documentação presentes nesta cópia — não são cobertura de testes nem confirmação de aceite do grupo.

## 1. Git: atualizar a máquina local, criar branches, comitar e entregar

### 1.1 Baixar referências de todas as branches e atualizar `dev`

Execute no PowerShell, Git Bash ou terminal a partir da pasta raiz do CandyLand:

```bash
git fetch --all --prune
git branch -a

git switch dev
git pull --ff-only origin dev
```

`git fetch --all --prune` atualiza as referências de todas as branches dos remotes configurados; `git branch -a` mostra branches locais e remotas. Para abrir uma branch remota que ainda não existe localmente, use `git switch --track origin/nome-da-branch`.

### 1.2 Criar sempre a branch de trabalho a partir de `dev`

```bash
git switch dev
git pull --ff-only origin dev
git switch -c feature/resumo-da-tarefa
```

Use prefixos coerentes: `feature/` para funcionalidade, `fix/` para correção e `docs/` para documentação. **Nunca crie uma nova feature a partir de `main`** e não desenvolva diretamente em `dev` ou `main`.

### 1.3 Validar, comitar e publicar a branch

Antes de comitar, rode os testes indicados na seção de ambiente e revise o diff:

```bash
git status
git diff --check
git diff

git add caminho/do/arquivo1 caminho/do/arquivo2
git commit -m "feat: descreve a mudança"
git push -u origin feature/resumo-da-tarefa
```

Abra um Pull Request da branch `feature/...` ou `fix/...` **para `dev`**. Revise o código, os testes e a documentação; só então faça o merge. Depois que o PR for integrado:

```bash
git switch dev
git pull --ff-only origin dev
git branch -d feature/resumo-da-tarefa
```

Apague a branch remota somente depois de confirmar que o PR foi integrado e que a equipe não precisa mais dela (`git push origin --delete feature/resumo-da-tarefa`).

### 1.4 GitHub CLI: instalar, autenticar, criar PR e mesclar pelo terminal

O GitHub CLI (`gh`) é um programa de sistema, não uma dependência Python. **Não adicione `gh` a `backend/requirements.txt`**: `pip` instala bibliotecas Python, enquanto o CLI é instalado uma vez no Windows. Os lançadores `.cmd` executam os scripts PowerShell com `-ExecutionPolicy Bypass` **somente no processo daquele comando**; assim, não é necessário liberar a política manualmente a cada terminal nem alterar a política global do Windows.

Para consultar o PR da branch atual, execute:

```powershell
.\scripts\gerenciar_pr.cmd -Acao StatusPR
```

O gerenciador procura `gh.exe` no `PATH` e nos caminhos comuns de instalação. Se não estiver instalado, tenta instalá-lo pelo WinGet. Se não houver sessão autenticada, inicia o login pelo navegador e confirma o estado da sessão. O caminho do CLI também é salvo no `PATH` do usuário quando possível, mas o próprio gerenciador usa o caminho completo do executável para não depender de terminais antigos do VS Code/Windows Terminal. Portanto, não é necessário executar `Instalar` ou `Autenticar` manualmente a cada terminal.

As ações explícitas continuam disponíveis quando forem necessárias:

```powershell
.\scripts\gerenciar_pr.cmd -Acao Instalar
.\scripts\gerenciar_pr.cmd -Acao Autenticar
.\scripts\gerenciar_pr.cmd -Acao Atualizar
```

Para cada nova tarefa, trabalhe numa branch criada a partir de `dev`, rode os testes, faça commit e push. Então crie e confira o PR:

```powershell
.\scripts\gerenciar_pr.cmd -Acao CriarPR -Titulo "feat: descreve a tarefa"
.\scripts\gerenciar_pr.cmd -Acao StatusPR
```

O script confirma que o repositório é o CandyLand esperado, que a branch está enviada ao `origin`, que a árvore de trabalho está limpa e que contém o `origin/dev` atual. Ele passa `--base dev` explicitamente, configura `dev` como base padrão local dessa branch e impede criar PR a partir de `dev` ou `main`. Se não houver PR aberto, `StatusPR` informa isso sem encerrar com erro; se já existir um PR para a branch, ele mostra o existente em vez de duplicá-lo.

Depois da revisão e do aceite necessários pela equipe, confira novamente o PR e faça o merge pelo terminal:

```powershell
.\scripts\gerenciar_pr.cmd -Acao StatusPR
.\scripts\gerenciar_pr.cmd -Acao MesclarPR -ConfirmarMerge
```

A segunda ação valida que o PR está aberto, que a origem é a branch atual e que o destino é `dev`; pede que você digite `MERGE` antes de integrar. O GitHub ainda pode bloquear a integração se as regras/revisões exigidas não estiverem satisfeitas. Após o merge, atualize e limpe a branch local:

```powershell
git switch dev
git pull --ff-only origin dev
git branch -d feature/nome-da-tarefa
```

O aviso amarelo do GitHub `dev had recent pushes — Compare & pull request` ao navegar em `main` é apenas uma sugestão automática. Como `main` permanece a branch padrão/de entrega de sprint, não altere essa configuração só para esconder o aviso: use o script, que fixa o destino `dev`.

### 1.5 Entregar `dev` em `main` somente no fechamento da sprint

No fluxo recomendado, abra um Pull Request **de `dev` para `main`** ao final da sprint, depois das validações e do aceite da equipe. Não integre feature diretamente em `main`.

Se a equipe realizar a entrega via merge local, sincronize as duas branches antes e confirme que a equipe concordou com esse procedimento:

```bash
git switch dev
git pull --ff-only origin dev

git switch main
git pull --ff-only origin main
git merge --no-ff dev
git push origin main

git switch dev
git pull --ff-only origin dev
```

O fluxo é sempre **`main` (entregas de sprint) ← `dev` (integração) ← `feature/*`/`fix/*`/`docs/*` (trabalho)**. Conflitos devem ser resolvidos na branch de trabalho ou durante o PR para `dev`, nunca escondidos por cópia manual de arquivos.

## 2. Veredito executivo

**Estado atual: MVP parcial, ainda não pronto para produção.** A base web, autenticação por código/OAuth, gestão de restaurante/produto, carrinho local e motor básico de estados de pedido existem. O fluxo de compra ainda não fecha de ponta a ponta, e há riscos de autorização na API que devem ser tratados antes de expandir o checkout.

### O que já temos

- Frontend web em React 19 com Vite 8, rotas de cliente e área de parceiros.
- API em Flask com SQLAlchemy e SQLite configurado como banco padrão no exemplo de ambiente.
- Modelos para usuários, endereços, restaurantes, categorias, produtos, pedidos, itens, entregas, cartões tokenizados e validação de autenticação: **11 modelos/tabelas**.
- CRUDs e telas para catálogo, categorias e configuração do restaurante.
- Login por código com serviços de e-mail (Brevo) e WhatsApp (Twilio), além de rotas para Google e Facebook.
- Carrinho em `localStorage` com inclusão pela tela de restaurante, alteração de quantidade e remoção.
- Criação/consulta/cancelamento de pedidos, validação de transições e código de serviço para baixar estoque na confirmação e repor em cancelamento.
- Regras de pedido e entrega em `docs/regras-pedidos.md`; modelo físico e diagrama em `docs/modelo-dados.md` e `docs/modelo-dados.png`.

### O que impede considerar o MVP concluído

1. **Segurança da API (prioridade imediata):** rotas de usuários e mutações de restaurante estão públicas no código atual; revisar leitura de dados pessoais, autenticação e autorização por papel/registro.
2. **Checkout não fecha:** o botão `Finalizar pedido` está desabilitado e não há tela de pagamento integrada.
3. **Confirmação do pagamento não tem rota pública/autenticada de integração:** `OrderService.confirmar_pagamento()` existe como método interno, mas não há endpoint/webhook para acioná-lo com segurança.
4. **Histórico logístico ainda incompleto:** a rota autenticada `PUT /pedidos/<id>/entrega/status` está implementada nesta entrega; ainda falta uma tabela de histórico auditável e um perfil próprio de entregador. O estado `ENTREGA_CONCLUIDA` agora sincroniza o pedido para `ENTREGUE` na mesma transação.
5. **Taxa de entrega:** a API calcula a taxa no servidor por Haversine, valida o raio configurado e ignora `delivery_fee` enviado pelo cliente. A distância cobrada fica registrada no pedido; a distância é em linha reta, não rota por ruas.
6. **Catálogo inconsistente:** o botão `Adicionar` em `Itens.jsx` não chama `adicionarItem`; a inclusão funciona somente na tela do restaurante.
7. **Testes e ferramentas:** a última validação local registrada para a frente de taxa por distância passou com 31 testes de regras de negócio em quatro arquivos (`python -m pytest tests/business_rules -q`). A suíte cobre regras, persistência, autorização de endpoint e taxa por distância, mas ainda não é end-to-end. A limpeza técnica substitui defaults `datetime.utcnow()` depreciados e encerra engines SQLite em memória sem `drop_all()` em fixtures com FKs cíclicas. Rode novamente os testes depois de aplicar essa limpeza.
8. **Operação/documentação pendente:** faltam documentação de endpoints, diagrama de arquitetura, Docker, notificação de pedidos, emissão fiscal e integrações reais de pagamento.

### Frente recomendada para atacar primeiro

**Frente 0 — segurança e testes da API.** Antes de habilitar pagamento, proteger endpoints de escrita/leitura sensível, manter apenas catálogo público explicitamente definido, testar papéis `PERSONAL` e `BUSINESS` e impedir que um cliente altere recursos de outra conta. É um bloqueio de segurança, não uma melhoria opcional.

Depois: **Frente 1 — fechar pedido sem gateway real** (carrinho → criar pedido → estado `PENDENTE_PAGAMENTO` → fluxo de pagamento em sandbox/mock isolado → confirmar por endpoint autenticado/evento confiável → baixar estoque uma única vez → cancelar/repor corretamente). Paralelamente, corrigir o botão da listagem de produtos e implementar a taxa de entrega no backend.

## 3. Tecnologias, ferramentas e integrações identificadas

| Camada | Tecnologias presentes no projeto | Observação |
|---|---|---|
| Linguagem backend | Python; alvo prático Python 3.10+ | O ambiente de auditoria usou Python 3.13, mas os testes não coletaram sem instalar dependências. |
| API | Flask 3.1.3, Flask-CORS 6.0.2 | **Não é FastAPI.** Rotas JSON definidas em blueprints. |
| ORM/banco | Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.43, SQLite pelo `.env.example` | Não há migration framework encontrado; `db.create_all()` não modifica tabelas existentes. PostgreSQL não foi validado nesta cópia. |
| Autenticação | PyJWT 2.9.0, Google Auth 2.40.3, `@react-oauth/google` | Google/Facebook dependem de configuração externa válida. |
| Mensageria | Requests 2.32.5, Twilio 9.10.5, integração HTTP Brevo | Serviços aparecem no código, mas notificação de eventos de pedido ainda não está ligada. |
| Frontend | React 19, React DOM 19, React Router 7 | Aplicação web, não aplicativo Android/iOS. |
| Build frontend | Node.js compatível com Vite 8 (`^20.19.0` ou `>=22.12.0`), npm 10+ recomendado, Vite 8.2.x, `@vitejs/plugin-react` 6.x | `npm run dev`, `npm run build`; não usar `npm start` (script não existe). |
| Utilitários frontend | `libphonenumber-js`, `@react-oauth/google` | Há também consulta de CEP ViaCEP no serviço de endereço. |
| Testes | pytest 8.4.2 | 31 testes de regras de negócio em quatro arquivos passaram na validação local da frente de taxa; ainda faltam testes mais amplos de segurança, checkout e ponta a ponta. |
| Ferramentas de desenvolvimento | Git, GitHub CLI (`gh`), PowerShell (`scripts/`), VS Code | `gh` é ferramenta externa do sistema, instalada via WinGet; não entra em `backend/requirements.txt`. As extensões recomendadas estão em `.vscode/extensions.json`; Docker, Swagger/OpenAPI e CI não foram encontrados. |
| Extensões VS Code recomendadas | Python, Pylance, ESLint, Prettier e PowerShell | São recomendações de workspace, não uma afirmação de que todos já estejam instalados nos computadores da equipe. |
| Integrações ausentes/incompletas | Google Maps Routes/Distance Matrix, gateway Mercado Pago/PayPal, push, NFe/SEFAZ, AWS | As integrações não devem ser descritas como concluídas só porque existe uma chave de configuração ou um modelo de dados. |

> **Manutenção desta seção:** ao adicionar, remover ou atualizar dependências, ajustar esta tabela e os arquivos de dependência (`backend/requirements.txt`, `frontend/package.json` e `frontend/package-lock.json`) no mesmo PR. Não colocar chaves reais no README nem no Git.

## 4. Preparar e executar o ambiente local (Windows/PowerShell)

Na raiz do projeto, execute o lançador:

```powershell
.\scripts\preparar_ambiente.cmd
```

O lançador aplica `-ExecutionPolicy Bypass` somente ao processo PowerShell iniciado para essa tarefa. Não é necessário liberar a política manualmente a cada terminal nem alterar a política global do Windows.

O script descobre a raiz pela própria localização, cria/reutiliza `.venv`, instala `backend/requirements.txt`, instala dependências do frontend com `npm ci` quando existe lockfile e executa o build. Ele cria `backend/.env` e `frontend/.env.local` a partir dos exemplos **somente se os arquivos não existirem**; não sobrescreve configurações locais.

Pré-requisitos: Git, PowerShell, Python 3.10+ e Node.js aceito pelo Vite 8. O script falhará com mensagem explícita se faltar um requisito. Para criar/mesclar PR pelo terminal, o gerenciador de PR tenta instalar o GitHub CLI automaticamente se necessário; isso é uma ferramenta de desenvolvimento e não é instalada pelo `pip`.

### Iniciar o backend

Em um terminal, na raiz do projeto:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe run.py
```

API local: `http://127.0.0.1:5000`.

### Iniciar o frontend

Em outro terminal, na raiz do projeto:

```powershell
Set-Location frontend
npm run dev
```

O frontend Vite informa no terminal o endereço local (padrão `http://localhost:5173`). Os serviços frontend atualmente contêm URLs de API fixas para `http://127.0.0.1:5000`; se isso mudar, centralizar a URL em variável `VITE_API_URL` e atualizar `.env.example`.

### Testes e build

```powershell
# Backend
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q

# Frontend: novo terminal ou volte à raiz
Set-Location ..\frontend
npm ci
npm run build
```

Não considerar o ambiente validado se os testes não rodarem. Guarde a saída de erro no PR, corrija-a e rode novamente. Não commitar `.env`, tokens, chaves, `node_modules`, `.venv`, banco local ou caches.

### Gerar ZIP limpo de compartilhamento

A partir da raiz, execute:

```powershell
.\scripts\gerar_zip_limpo.cmd
```

O ZIP é criado na raiz e contém o código/documentação, mantendo dotfiles de exemplo como `.gitignore` e `.env.example`. O script exclui arquivos `.env` reais, bancos locais, credenciais, `.git`, ambientes virtuais, `node_modules`, caches, builds e outros ZIPs. **Ele não apaga nem limpa nenhum arquivo original do projeto.**

## 5. Regras de manutenção obrigatória

- Toda regra de negócio acordada deve ser registrada em `docs/requisitos.md`; o ciclo detalhado de pedidos/entregas fica em `docs/regras-pedidos.md`.
- Toda alteração em tabela, coluna, chave estrangeira, default persistido ou relacionamento exige atualização de `docs/modelo-dados.md`, `docs/modelo-dados.dot` e `docs/modelo-dados.png` no mesmo PR.
- Todo comportamento novo de pedido exige testes em `backend/tests/business_rules/` e, quando envolver rota/segurança, testes de endpoint.
- Os percentuais abaixo só sobem quando houver evidência no código e, idealmente, teste automatizado. Uma tela isolada não significa que o fluxo completo está pronto.
- Não apagar nem recriar banco de dados para “atualizar o modelo”. `db.create_all()` cria tabelas ausentes, mas não migra tabelas já existentes. Mudanças físicas futuras devem ter backup e uma migração explícita; não há Alembic/configuração de migração identificado neste repositório.
- Para modelos que guardam padrão no lado Python, como `Pedido.status`, alinhar o default com a regra. A correção `CREATED` → `PENDENTE_PAGAMENTO` não apaga nem atualiza pedidos já existentes.
- Para datas UTC em colunas `DateTime` legadas sem timezone, usar `app.utils.datetime_utils.utc_now_naive`; não usar `datetime.utcnow()`, depreciado no Python 3.12+. A migração para colunas timezone-aware deve ser tratada separadamente.
- Fixtures com SQLite em memória e app exclusiva devem encerrar a sessão e descartar o engine (`db.session.remove(); db.engine.dispose()`). Evitar `db.drop_all()` no teardown quando há FKs cíclicas que o SQLite não consegue alterar para ordenar o DROP; o banco em memória será descartado ao liberar o engine.
- Nunca armazenar número completo/CVV de cartão. Usar token/metadados de provedor e escolher formalmente o gateway antes da integração.

### Configuração e validação de login Google e Facebook

O código de autenticação OAuth depende de configuração válida nos painéis dos provedores. A existência das rotas ou dos botões de login, isoladamente, não comprova que o login está operacional.

#### Google OAuth

- Configurar `VITE_GOOGLE_CLIENT_ID` em `frontend/.env.local`.
- Configurar `GOOGLE_CLIENT_ID` em `backend/.env`.
- Os dois IDs devem corresponder ao mesmo cliente OAuth.
- Cadastrar os domínios autorizados e os URIs de redirecionamento exigidos pelo fluxo utilizado.
- Em ambiente de teste, autorizar as contas de teste no painel Google Cloud quando necessário.

#### Facebook Login

- Configurar `FACEBOOK_CLIENT_ID` e `FACEBOOK_CLIENT_SECRET` em `backend/.env`.
- Configurar `FACEBOOK_REDIRECT_URI` com o endereço exato usado pelo backend e cadastrado no painel Meta.
- Conferir o modo do aplicativo, os usuários com funções de teste e as permissões solicitadas.
- Antes da publicação, configurar os domínios e URLs de produção e verificar os requisitos de acesso do aplicativo.

#### Validação e segurança

- Testar cada provedor separadamente com uma conta autorizada.
- Validar login bem-sucedido, cancelamento e falha de autenticação.
- Não registrar tokens, client secrets ou credenciais nos logs, no README ou no Git.
- Manter valores reais apenas nos arquivos locais de ambiente ou no gerenciador de segredos do serviço publicado.
- A conclusão da tarefa exige evidência de login funcionando; variáveis preenchidas não são suficientes.
- A configuração local e a configuração de produção devem ser verificadas separadamente. Não presumir que um login local validado já está pronto para publicação.

## 6. Mapa de funcionalidades — percentual auditado

**Critério:** percentual estimado de entrega da funcionalidade, não percentual de linhas codificadas. `0%` significa que a implementação não foi encontrada nesta cópia; `100%` significa que o entregável descrito foi encontrado/documentado, não que todo o produto ou uma versão futura ideal esteja pronto. Itens de integração externa só contam como concluídos após teste com o provedor.

| # | Frente | Funcionalidade | Prioridade | % atual | Objetivo/critério de conclusão | Lacuna identificada e próxima ação |
|---:|---|---|:---:|---:|---|---|
| 1 | Documentação funcional | Explicação detalhada das funcionalidades | P1 | 90% | Os requisitos e as regras de pedidos estão descritos em Markdown. | Ainda não há especificação completa de todos os endpoints, fluxos de erro e critérios de aceite. Próxima ação: Completar critérios de aceite e ligar cada requisito a endpoint e teste. |
| 2 | Documentação funcional | Diagrama de arquitetura | P1 | 0% | Não foi encontrado diagrama de arquitetura no repositório atual. | A arquitetura fica implícita no código; não há diagrama entregue no ZIP. Próxima ação: Criar diagrama de frontend, API, autenticação, provedores externos e banco. |
| 3 | Banco de dados | Diagrama do modelo físico atual | P1 | 100% | Os 11 modelos SQLAlchemy foram mapeados e o diagrama atual foi criado em docs/modelo-dados.png. | O modelo atual está documentado; redesign de endereços, histórico e pagamento continua futuro. Próxima ação: Atualizar Markdown, fonte DOT e PNG em toda alteração estrutural. |
| 4 | Documentação funcional | Documento geral do projeto | P1 | 90% | README atualizado com tecnologia real, setup, Git flow, estado do produto e plano. | A documentação OpenAPI/endpoints e critérios de aceite por história ainda faltam. Próxima ação: Documentar os endpoints e manter as duas tabelas no README em cada entrega. |
| 5 | Autenticação | Cadastro de usuários | P2 | 80% | Existem tela de cadastro, rotas de usuário e fluxo de código de autenticação. | Endpoints de usuários ainda permitem operações sem token; falta teste ponta a ponta de cadastro verificado. Próxima ação: Restringir escrita e garantir que cadastro só seja concluído após validação. |
| 6 | Autenticação | Login por celular | P2 | 80% | O fluxo de código e serviço WhatsApp/Twilio existem. | Entrega, expiração e limites de tentativas precisam de teste integrado com credenciais válidas. Próxima ação: Cobrir expiração, reenvio, tentativas e falha do provedor. |
| 7 | Autenticação | Login por e-mail | P2 | 80% | O serviço Brevo e os endpoints de códigos estão presentes. | A integração depende de variáveis externas e não há teste end-to-end no repositório. Próxima ação: Testar envio e verificação com provedor simulado e variáveis ausentes. |
| 8 | Autenticação | Código de validação em login/cadastro | P2 | 80% | Modelos auth_codes/auth_attempts e rotas de verificação existem. | Falta fechar controles de abuso, fluxo completo e cobertura de integração. Próxima ação: Adicionar testes de código expirado, reutilizado, incorreto e limite de tentativas. |
| 9 | Autenticação | Integração Google (login OAuth) | P2 | 85% | O backend contém serviço Google e a interface usa @react-oauth/google. | Requer client ID válido e teste real de ponta a ponta. Próxima ação: Documentar configuração, validar audience/issuer e testar falhas de credencial. |
| 10 | Autenticação | Integração Facebook | P2 | 65% | Rotas de login, callback e conclusão existem no backend. | Depende de credenciais/redirect URI; integração não comprovada por testes no ZIP. Próxima ação: Validar callback, estado, configuração e cenários de erro. |
| 11 | Endereço | Cadastro de locais + Google Maps | P2 | 25% | Há modelo de endereço, campos de latitude/longitude e consulta de CEP ViaCEP. | Não foi encontrado serviço/endpoint completo de autocomplete, geocodificação ou mapa Google. Próxima ação: Definir API de endereço e concluir seleção/geocodificação com testes. |
| 12 | Restaurante | CRUD de restaurante | P2 | 65% | Há controllers, services e rotas de criar/listar/consultar/alterar/excluir. | Rotas de escrita CRUD estão públicas e faltam testes de autorização e validação. Próxima ação: Proteger mutações por token/conta BUSINESS e testar isolamento por restaurante. |
| 13 | Restaurante | Configuração dos dados do restaurante | P2 | 85% | Tela React e endpoints dedicados de consulta/atualização existem com checagem da conta. | Faltam testes automatizados e validação mais robusta dos limites/regras. Próxima ação: Adicionar testes de autorização, faixa de entrega, taxa e dados inválidos. |
| 14 | Catálogo | CRUD de produto | P2 | 80% | Existem formulário e rotas de criar/listar/consultar/alterar/excluir, além de estoque e image_url. | Upload de imagem não existe; é armazenada uma URL; autorização das mutações precisa ser validada. Próxima ação: Fechar autorização BUSINESS, testes e fluxo de upload/armazenamento de imagem. |
| 15 | Catálogo | Lista de restaurantes | P3 | 85% | Home/Landing consomem GET /restaurantes e exibem lojas. | Busca por proximidade/endereço não é real e depende de cálculo geográfico ainda ausente. Próxima ação: Adicionar filtros reais e estados vazios/erro testados. |
| 16 | Catálogo | Lista e seleção de produtos | P3 | 75% | Tela de itens busca produtos, filtra por loja/termo e ordena por preço. | O botão Adicionar da tela geral não tem handler; inclusão funciona na tela do restaurante. Próxima ação: Unificar ação de adicionar ao carrinho e bloquear produto sem estoque/disponibilidade. |
| 17 | Carrinho | Inclusão de produto no carrinho | P4 | 70% | CartContext guarda itens e a tela do restaurante chama adicionarItem. | A tela geral de itens não aciona a ação; não há validação de estoque no carrinho. Próxima ação: Conectar botão da listagem e revalidar preço/estoque no backend. |
| 18 | Carrinho | Exclusão de produto do carrinho | P4 | 95% | Há função removerItem, botão de remoção e persistência em localStorage. | Falta cobertura automatizada de interface e reconciliação com checkout. Próxima ação: Adicionar testes de UI e limpar corretamente ao concluir/cancelar compra. |
| 19 | Carrinho | Alteração de quantidade | P4 | 95% | Os botões +/- alteram quantidade e quantidade zero remove o item. | Falta teste de UI e validação posterior no estoque do servidor. Próxima ação: Cobrir limites e validar novamente no endpoint de pedido. |
| 20 | Checkout | Escolha da forma de pagamento | P5 | 25% | A API aceita PIX e CARTAO_CREDITO ao criar pedido. | Não existe tela de checkout funcional; o botão Finalizar pedido está desabilitado. Próxima ação: Criar tela de checkout e persistir a opção escolhida após validação do pedido. |
| 21 | Checkout | Integração de pagamento com cartão | P5 | 5% | Existe modelo customer_cards para referência tokenizada; não há gateway conectado. | Não há integração Mercado Pago/PayPal nem webhook de confirmação. Próxima ação: Escolher provedor, implementar criação de pagamento, webhook idempotente e testes sandbox. |
| 22 | Checkout | Seleção do tipo de entrega | P5 | 75% | Carrinho permite escolher `DELIVERY` ou `PICKUP`, salva a opção e o backend valida o tipo; retirada usa o endereço ativo do restaurante e não gera taxa/registro logístico. | A finalização segue desabilitada e ainda não envia essa opção à API. Próxima ação: integrar seleção ao checkout quando a tarefa de finalização for iniciada. |
| 23 | Checkout | Notificação push de novo pedido | P5 | 0% | Não há fluxo push identificado. | Sem provedor, registro de token de dispositivo ou evento de pedido novo. Próxima ação: Definir estratégia de notificação e implementar após o ciclo de pedido estável. |
| 24 | Checkout | Envio de nota fiscal PDF por e-mail | P5 | 0% | Não foi encontrada emissão fiscal ou geração de PDF de nota. | Integração fiscal e documento não existem. Próxima ação: Definir requisito fiscal e integração aprovada antes de implementar. |
| 25 | Pedidos | CRUD, validações, testes, estoque e persistência | P5 | 65% | Serviço cria/lista/consulta/cancela pedidos, valida transições e expõe atualização de estado principal e logístico. | Não existe endpoint de confirmação de pagamento, update/delete genérico, histórico de estados nem testes suficientes de estoque/duplicidade. Próxima ação: proteger confirmação de pagamento e ampliar testes transacionais. |
| 26 | Entrega | Push a cada mudança de status | P6 | 0% | Não há integração push ligada à máquina de estados. | Nenhum evento de notificação para transições. Próxima ação: Criar eventos de domínio e provedor após persistência confiável dos estados. |
| 27 | Entrega | Alteração/persistência do status do pedido e entrega | P6 | 80% | Há máquina de estados, rota autenticada para `PUT /pedidos/<id>/entrega/status`, autorização para o restaurante dono do pedido e sincronização transacional de `ENTREGA_CONCLUIDA` para `ENTREGUE`. | Histórico de transições e papel de entregador ainda não existem; falta teste ponta a ponta e política para atualização por motorista. Próxima ação: decidir tabela de auditoria e perfil de ator. |
| 28 | Entrega | Tela de acompanhamento da entrega | P6 | 0% | Não há tela de acompanhamento identificada em App.jsx. | Falta UX de timeline/estado e atualização em tempo real ou polling. Próxima ação: Criar tela após endpoint de entrega e contrato de status estáveis. |
| 29 | Entrega | Código de validação do entregador | P6 | 0% | Não há modelo, endpoint ou interface de código de retirada/entrega. | Faltam geração segura, expiração e validação única. Próxima ação: Definir regra do código e registrar tentativa/consumo. |
| 30 | Restaurante | Painel do restaurante | P5 | 40% | Existe home de parceiros e telas de cardápio, produto, categoria e configuração. | Não há tela/fluxo operacional completo para receber e atualizar pedidos. Próxima ação: Priorizar painel de pedidos após proteger rotas de escrita. |
| 31 | Infraestrutura | AWS (IA/Lambda/banco) | P7 | 0% | Não foram encontrados manifests ou código de deploy AWS. | Sem arquitetura cloud, pipeline, secrets management ou ambiente de homologação. Próxima ação: Definir requisitos não funcionais e infraestrutura somente após estabilizar MVP. |
| 32 | Fiscal | NFe / SEFAZ | P7 | 0% | Nenhuma integração SEFAZ/emissão NFe identificada. | Falta levantamento fiscal e provedor homologado. Próxima ação: Levantar obrigações fiscais e escolher solução autorizada. |
| 33 | Relatórios | Esboço de três relatórios | P7 | 0% | Não foram localizados protótipos de relatórios no repositório. | Faltam perguntas de negócio, público e métricas. Próxima ação: Definir relatórios com stakeholders e critérios de aceite. |
| 34 | Relatórios | Implementação de três relatórios | P7 | 0% | Não foram encontradas telas/rotas de relatórios. | Depende dos requisitos e dados consolidados. Próxima ação: Implementar após definir métricas e permissões. |
| 35 | Comunicação | SMS/WhatsApp/e-mail automáticos | P7 | 25% | Serviços Brevo e Twilio/WhatsApp existem para código de autenticação. | Notificações de pedido/entrega e tratamento de falha não estão conectados ao ciclo do pedido. Próxima ação: Generalizar eventos/notificações com retries, logs e templates. |
| 36 | Integrações | Integração automática com redes sociais | P7 | 0% | Não foi encontrada integração operacional de publicação. | Escopo, plataformas e permissões não definidos. Próxima ação: Definir objetivo e APIs antes de priorizar. |
| 37 | Mapas | Cálculo de caminho mínimo Google Maps | P7 | 5% | Há campos latitude/longitude e configuração de chave de Maps no exemplo. | Não existe chamada de Routes/Distance Matrix nem cálculo de rota no código. Próxima ação: Implementar cálculo server-side com tratamento de limites e testes. |
| 38 | Pagamento | Cartões / Mercado Pago | P5 | 10% | Há modalidade de cartão e modelo de cartão tokenizado planejado. | Não há SDK, criação de cobrança, webhook nem vínculo pagamento-pedido. Próxima ação: Escolher Mercado Pago ou PayPal; evitar dados brutos de cartão no CandyLand. |
| 39 | Mobile | Aplicativo mobile | P7 | 0% | O projeto atual contém frontend React web, não app mobile. | Sem projeto Android/iOS ou estratégia PWA declarada. Próxima ação: Reavaliar após validar uso e fluxo web MVP. |
| 40 | Operação | Leitor de código de barras | P7 | 0% | Não há leitor/fluxo de barcode identificado. | Hardware, UX e caso de uso não definidos. Próxima ação: Definir se é para estoque ou venda e especificar equipamento/API. |
| 41 | Operação | Painel/dispositivo de chamada para retirada | P7 | 0% | Não há fluxo de pedido para retirada nem painel de chamada. | Depende da decisão de entrega/retirada e de um estado de pronto. Próxima ação: Definir fluxo RETIRADA antes do painel. |
| 42 | Pagamento | Pagamento via Pix | P5 | 5% | PIX é aceito como valor de payment_method no backend. | Sem geração de QR Code Pix, cobrança, confirmação ou conciliação. Próxima ação: Implementar Pix por gateway e webhook idempotente no fluxo de checkout. |
| 43 | Operação | Leitor de QR Code | P7 | 0% | Não há leitura de QR Code em frontend ou backend. | Uso e validação do conteúdo não definidos. Próxima ação: Definir caso de uso e regra de segurança. |
| 44 | Estoque | Estoque, baixa após pagamento e reposição em cancelamento | P5 | 60% | Produto mantém current_stock; pedido valida quantidade; confirmar_pagamento debita e cancelamento após pagamento repõe. | Confirmação não está exposta por rota, teste de estoque é insuficiente e concorrência não foi validada. Próxima ação: Adicionar endpoint autenticado/webhook, transação e testes de duplicidade/concor­rência. |
| 45 | Catálogo | Sugestão de produtos | P7 | 0% | Não foi encontrado recomendador nem regra de produtos relacionados. | Sem critérios (popularidade, categoria ou histórico) e sem interface. Próxima ação: Começar por recomendações simples por categoria quando houver dados. |
| 46 | Entrega | Taxa de entrega por distância | P5 | 75% | Taxa calculada no backend: taxa base + distância Haversine × taxa por km, dentro do raio do restaurante. | Falta validar UX ponta a ponta e disponibilizar edição de coordenadas para endereços antigos (gerenciamento de endereços está atribuído a outro integrante); Haversine mede linha reta, não rota viária. |

## 7. Planejamento por responsável — Sprint 3 (23/09 a 19/10/2026)

Esta tabela consolida as linhas de planejamento fornecidas pela equipe, mantendo os responsáveis. O **status informado** é o status reportado no planejamento; a coluna **auditoria/evidência** registra o que foi possível confirmar no código/arquivos deste ZIP. Documentos `.docx` ausentes do ZIP podem existir fora do repositório; não foram considerados verificados. A linha duplicada de informações pessoais foi consolidada porque tinha status conflitante.

| Sprint | História | Atividade/entregável | Branch de trabalho | Arquivo/evidência | Responsável | Status informado | Auditoria/percentual estimado | Entrega prevista |
|---|---|---|---|---|---|---|---|
| Sprint 3 (23/09–19/10) | Documentação | Levantamento de Requisitos - Produto (Documento) | `—` | `Levantamento_Requisitos_Produto.docx` | Ana Carolina Guedes Bueno | Concluído (informado) | 100% informado; DOCX não incluído no ZIP auditado. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Documentação | Levantamento de Requisitos - Cliente (Documento) | `—` | `Levantamento_Requisitos_Cliente.docx` | Ana Carolina Guedes Bueno | Concluído (informado) | 100% informado; DOCX não incluído no ZIP auditado. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Documentação | Levantamento de Requisitos - Endereço (Documento) | `—` | `Levantamento_Requisitos_Endereco.docx` | Ana Carolina Guedes Bueno | Concluído (informado) | 100% informado; DOCX não incluído no ZIP auditado. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Documentação | Atualização - Carrinho (Documento) | `—` | `Levantamento_Requisitos_Carrinho.docx` | Ana Carolina Guedes Bueno | Concluído (informado) | 100% informado; DOCX não incluído no ZIP auditado. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Documentação | Atualização - Categoria (Documento) | `—` | `Levantamento_Requisitos_Categoria.docx` | Kauan Felipe Dutra de Almeida | Concluído (informado) | 100% informado; DOCX não incluído no ZIP auditado. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Documentação | Levantamento de Requisitos - Doceria (Documento) | `—` | `Levantamento_Requisitos_Doceria.docx` | Kauan Felipe Dutra de Almeida | Concluído (informado) | 100% informado; DOCX não incluído no ZIP auditado. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Documentação | Levantamento de Requisitos - Cartão Cliente (Documento) | `—` | `Levantamento_Requisitos_CartaoCliente.docx` | Kauan Felipe Dutra de Almeida | Concluído (informado) | 100% informado; DOCX não incluído no ZIP auditado. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Restaurante | Tela de Pedidos do Restaurante - Frontend (Código React) | `—` | `Tela/rota de pedidos não encontrada` | Julia Parreiras Fagundes do Nascimento | Não iniciado | 0%; App.jsx não tem rota de operação de pedidos. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Restaurante | Tela de Cardápio do Restaurante - Frontend (Código React) | `—` | `frontend/src/pages/Cardapio.jsx` | Maria Eduarda Gomes Romera | Concluído (informado) | 90%; componente existe; falta teste UI e validação ponta a ponta. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Restaurante | Tela de Configuração de Dados do Restaurante - Frontend (Código React) | `—` | `frontend/src/pages/RestaurantConfiguration.jsx` | Theofilo Fernandes de Mesquita | Concluído (informado) | 85%; tela/API presentes; falta cobertura de testes e validações de regra. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Restaurante | Tela Home Parceiros - Frontend (Código React) | `—` | `frontend/src/pages/BusinessHome.jsx` | Yuri Gabriel Conceição Gonçalves | Concluído (informado) | 80%; home e atalhos existem, mas painel de pedidos não. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Login | Ajuste Home Cliente - Frontend (Código React) | `—` | `frontend/src/pages/Home.jsx` | Maria Eduarda Gomes Romera | Concluído (informado) | 90%; página existe e consome API de restaurantes. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Carrinho | Protótipo de carrinho (Documento/protótipo) | `—` | `Documento de protótipo não localizado` | Julia Parreiras Fagundes do Nascimento | Não iniciado (informado) | 30%; há tela funcional parcial, mas protótipo como entregável não foi localizado. | 2026-09-30 |
| Sprint 3 (23/09–19/10) | Cadastro Usuário | Protótipo - Cadastro de Método de Pagamento (Documento) | `—` | `Documento não localizado` | Julia Parreiras Fagundes do Nascimento | Não iniciado | 0%; checkout e escolha de pagamento não implementados no frontend. | 2026-10-07 |
| Sprint 3 (23/09–19/10) | Cadastro Usuário | Protótipo - Gerenciamento de Endereço (Documento/protótipo) | `—` | `Documento não localizado; addressService.js presente` | Kauan Felipe Dutra de Almeida | Em andamento (informado) | 40%; consulta de CEP existe, mas Maps e integração completa não. | 2026-10-07 |
| Sprint 3 (23/09–19/10) | Carrinho | CRUD - Frontend (Código React) | `—` | `frontend/src/context/CartContext.jsx; frontend/src/pages/Cart.jsx` | Yuri Gabriel Conceição Gonçalves | Concluído (informado) | 70%; alterar/remover/persistir funciona; adicionar na listagem geral está desconectado e checkout não existe. | 2026-10-07 |
| Sprint 3 (23/09–19/10) | Documentação | Autenticação Google Maps (Documento) | `—` | `Atenticação Google Maps.docx não localizado` | Ana Carolina Guedes Bueno | Concluído (informado) | Não verificável neste ZIP; não há serviço Google Maps completo no código atual. | 2026-10-07 |
| Sprint 3 (23/09–19/10) | Pedidos | CRUD - Backend (Código Python) | `—` | `backend/app/routes/order_routes.py; backend/app/services/order_service.py` | Theofilo Fernandes de Mesquita | Concluído (informado) | 70%; create/list/detail/status/cancel e endpoint de status logístico existem; confirmação de pagamento segue sem rota. | 2026-10-07 |
| Sprint 3 (23/09–19/10) | Pedidos | Regras de fluxo, cancelamento e estoque (Código Python) | `feature/orders-crud` | `backend/app/services/order_workflow_service.py; backend/app/services/order_service.py` | Theofilo Fernandes de Mesquita | Concluído (informado) | 70%; transições e serviços de estoque existem; confirmação por provedor e testes de estoque/duplicidade ainda faltam. | 2026-10-07 |
| Sprint 3 (23/09–19/10) | Cadastro Usuário | Tela de Dados - Informações Pessoais - Frontend (Código React) | `—` | `frontend/src/pages/PersonalRegister.jsx` | Maria Eduarda Gomes Romera | Em andamento (50% informado) | 70% estimado pelo código; consolidada aqui para eliminar a linha duplicada conflitante na planilha. | 2026-10-07 |
| Sprint 3 (23/09–19/10) | Pedidos | Implementação da seleção do tipo de entrega (Código Python/React) | `feature/tipo-entrega-pedido` (integrada em `dev`) | `Cart.jsx; CartContext.jsx; order_service.py; test_order_type.py` | Theofilo Fernandes de Mesquita | Integrada em `dev`; checkout pendente | 75%; seleção persistida no carrinho e suporte `DELIVERY`/`PICKUP` na API. Falta integrar ao checkout, que permanece desabilitado. | 2026-10-19 |
| Sprint 3 (23/09–19/10) | Pedidos | Integração e persistência dos estados do pedido e entrega (Código Python) | `feature/persistencia-status-entrega` (integrada em `dev`) | `order_routes.py; order_controller.py; order_service.py; test_order_delivery_persistence.py` | Theofilo Fernandes de Mesquita | Integrada em `dev` | 80%; endpoint autenticado com autorização por restaurante, persistência e sincronização do estado final. Falta histórico auditável, papel de entregador e validação ponta a ponta. | 2026-10-19 |
| Sprint 3 (23/09–19/10) | Pedidos | Implementação do cálculo da taxa de entrega por distância (Python/React/SQLAlchemy) | `feature/taxa-entrega-distancia` (esta branch) | `order_service.py; restaurant_service.py; AddressCoordinates.jsx; test_delivery_fee.py; migrations.py` | Theofilo Fernandes de Mesquita | Implementado nesta branch; aguarda testes e PR | 75%; taxa calculada no servidor, coordenadas e configuração adicionadas, migração aditiva e testes; checkout completo e UX com endereços reais continuam pendentes. | 2026-10-19 |
| Sprint 3 (23/09–19/10) | Produto | Inserir fluxo de adicionar foto para o produto cadastrado (Código Python/React) | `—` | `Produto.image_url; ProductForm.jsx` | Yuri Gabriel Conceição Gonçalves | Não iniciado | 30%; campo URL existe, não há upload/armazenamento de arquivo. | 2026-10-19 |
| Sprint 3 (23/09–19/10) | Documentação | Documentar os endpoints da aplicação (Documento) | `—` | `Não localizado; README lista rotas principais` | Ana Carolina Guedes Bueno | Não iniciado | 0%; falta catálogo de endpoints, payloads, autenticação e códigos de erro. | 2026-10-19 |
| Sprint 3 (23/09–19/10) | Docker | Criar configuração de Docker - Frontend (Dockerfile/Compose) | `—` | `Nenhum Dockerfile encontrado` | Kauan Felipe Dutra de Almeida | Não iniciado | 0%; não existe configuração Docker no repositório auditado. | 2026-10-19 |
| Sprint 3 (23/09–19/10) | Docker | Criar configuração de Docker - Backend (Dockerfile/Compose) | `—` | `Nenhum Dockerfile encontrado` | Maria Eduarda Gomes Romera | Não iniciado | 0%; não existe configuração Docker no repositório auditado. | 2026-10-19 |
| Sprint 3 (23/09–19/10) | Pagamento | Integração API PayPal - Backend (Código Python) | `—` | `Nenhuma integração PayPal encontrada` | Maria Eduarda Gomes Romera | Não iniciado | 0%; provedor não decidido nem implementado. | 2026-10-19 |
| Sprint 3 (23/09–19/10) | Diagrama | Arrumar infraestrutura do Diagrama de Arquitetura (Documento/diagrama) | `—` | `Diagrama de arquitetura não localizado` | Yuri Gabriel Conceição Gonçalves | Não iniciado | 0%; diagrama é entrega pendente; somente o diagrama ER foi atualizado. | 2026-10-19 |


## 8. Próximas entregas sugeridas

| Ordem | Entrega | Critérios de pronto |
|---:|---|---|
| 1 — bloqueador | Segurança das rotas e testes de autorização | Rotas de escrita exigem autenticação; conta `PERSONAL` não modifica dados de `BUSINESS`; usuários só consultam os próprios dados; catálogo público explicitamente permitido; testes 401/403/200. |
| 2 | Fechar carrinho e contrato de pedido | Botão de adicionar funciona na listagem; servidor recalcula preços/taxas e verifica disponibilidade/estoque; checkout valida endereço pertencente ao cliente. |
| 3 | Pagamento e estoque idempotentes | Decisão formal de provedor; confirmação não pode ser chamada publicamente por qualquer pessoa; webhook/evento verificado; pagamento duplicado não debita estoque duas vezes; cancelamento repõe corretamente uma única vez. |
| 4 | Histórico da entrega e papéis | Endpoint autenticado já existe; falta histórico de transições, papel de entregador e testes ponta a ponta do ciclo completo. |
| 5 | Painel do restaurante e experiência do cliente | Lista operacional de pedidos, estados, acompanhamento e notificações integradas. |
| 6 | Integrações e entrega de sprint | Gateway real, notificação e fiscal apenas quando requisitos e credenciais de homologação estiverem definidos. O cálculo de taxa em linha reta já foi implementado; rota viária é uma melhoria futura. |

## 9. Decisões pendentes do grupo

1. **Gateway de pagamento:** o plano cita PayPal, enquanto o escopo cita Mercado Pago. Escolher uma integração inicial; Pix/cartão são modalidades, gateways são provedores.
2. **Entrega vs. retirada:** este branch implementa `DELIVERY` e `PICKUP` como proposta para o MVP, com taxa zero e sem fluxo logístico para retirada. A equipe deve ratificar a regra antes do merge; o painel de chamada continua fora desta tarefa.
3. **Taxa de entrega:** regra definida: taxa base + (distância Haversine em linha reta × taxa por km), arredondada a centavos. O backend valida o raio e não aceita taxa enviada pelo cliente. Cliente e restaurante precisam cadastrar coordenadas válidas; o cálculo por rota viária continua fora do escopo desta regra.
4. **Histórico/auditoria do pedido:** definir se será tabela própria de eventos e quais atores podem executar cada transição.
5. **Banco legado:** escolher ferramenta de migração antes de mudanças estruturais. Fazer backup antes de qualquer migração; não remover tabelas nem apagar o banco local para resolver divergência documental.

## 10. Arquivos de referência

- `docs/requisitos.md` — regras globais e decisões de negócio.
- `docs/regras-pedidos.md` — estados e transições de pedido/entrega, cancelamento e pagamento.
- `docs/modelo-dados.md` — modelo físico atual, lacunas e instruções de atualização.
- `docs/modelo-dados.dot` e `docs/modelo-dados.png` — fonte editável e imagem legível do diagrama ER atual.
- `backend/app/database/migrations.py` — migração aditiva e idempotente das colunas de taxa/distância; a inicialização executa antes de consultar pedidos, sem apagar dados existentes.
- `scripts/preparar_ambiente.cmd` e `scripts/preparar_ambiente.ps1` — lançador seguro e instalação/verificação local sem sobrescrever `.env` existente.
- `scripts/gerenciar_pr.cmd` e `scripts/gerenciar_pr.ps1` — localiza/instala o GitHub CLI, verifica ou inicia autenticação, cria PR para `dev`, consulta status e permite merge explícito após revisão.
- `scripts/gerar_zip_limpo.cmd` e `scripts/gerar_zip_limpo.ps1` — geração de ZIP de compartilhamento sem apagar o projeto original.
- `limpar_e_gerar_zip.cmd` e `limpar_e_gerar_zip.ps1` — atalho legado seguro que delega para o gerador; não remove `.venv`, `node_modules`, bancos ou arquivos `.env`.


### Compartilhar celular entre conta pessoal e restaurante (somente desenvolvimento/testes)

No `backend/.env`, use `APP_ENV=development` e `ALLOW_DUPLICATE_PHONE=true`; depois reinicie o backend. Assim, uma conta `PERSONAL` e uma conta `BUSINESS` podem compartilhar o mesmo celular. O e-mail verificado continua único globalmente e é o que define a conta autenticada.

**Produção:** configure `APP_ENV=production`. Nesse ambiente o backend bloqueia a duplicidade mesmo que `ALLOW_DUPLICATE_PHONE=true` tenha sido definido por engano. Se `APP_ENV` não estiver configurado, o backend assume `production` por segurança. Valores aceitos para a flag booleana: `true`, `1`, `yes` e `on`.

A regra é aplicada ao cadastro por e-mail/WhatsApp, ao cadastro via OAuth e à alteração do telefone de um usuário. A validação do e-mail é global entre clientes e restaurantes.
