# CandyLand — Backlog atualizado por evidência de código

**Revisão:** 25/10/2026.
**Regra:** status abaixo considera o código e as evidências de teste/PR disponíveis; percentuais do backlog original foram corrigidos quando estavam desatualizados ou contradiziam a implementação observada. Percentuais são estimativas de entrega funcional, não cobertura de testes.

## Sprint 4 — entrega principal

| Prioridade | Atividade | Status revisado | Estimativa | Próximo passo / critério de aceite | Branch |
|---|---|---|---:|---|---|
| P0 | Proteção da API e testes de autorização | Concluído, PR #25 mesclado em `dev` | 100% da tarefa de segurança entregue | Manter regressões no conjunto de testes; revisar segurança final antes de produção | `feature/api-security-hardening` |
| P0 | Resolver identidade/e-mail e telefone compartilhado em testes | Concluído, PR #23 mesclado em `dev` | 100% da correção entregue | Preservar a regra: duplicidade só permitida em ambientes dev/testing/local e com flag ativa; em produção bloquear | `fix/auth-account-resolution` |
| P0 | Checkout mínimo: carrinho + API + endereço + modalidade + pedido pendente | Concluído, PR #26 mesclado em `dev` | 100% do checkout mínimo (sem cobrança real) | Manter os 7 testes de integração, suíte e build; validar no navegador no roteiro de fumaça | `feature/checkout-mvp` |
| P0 | Teste de fumaça integrado do MVP publicado | Testes automatizados aprovados; validação manual no browser pendente | 80% estimado | Executar o roteiro manual com login local/provedor configurado e registrar evidências de DELIVERY/PICKUP; manter suíte integrada/regressão | `fix/teste-integracao-mvp` (PR #27 mesclado) |
| P0 | Endurecer e validar Google OAuth local e preparar produção | Validação de ID token no backend; testes automatizados adicionados; credenciais reais ainda não validadas | 70% estimado | Configurar o mesmo Client ID no backend/frontend, cadastrar origem autorizada e validar login real nos ambientes local e de homologação | `feature/oauth-validation` |
| P0 | Endurecer e validar Facebook OAuth local e preparar produção | State anti-CSRF e testes automatizados adicionados; credenciais reais ainda não validadas | 70% estimado | Alinhar host do frontend/API/callback, validar URL no painel Meta e executar sucesso, cancelamento e state inválido com provedor real | `feature/oauth-validation` |
| P1 | CRUD, validação e estados do pedido/entrega | Backend implementado; integração de ponta a ponta pendente | 75% estimado | Testar transições por perfil, autorização e fluxo completo com checkout | Pode integrar a `feature/checkout-mvp` apenas se necessário; não recriar serviços já existentes |
| P1 | Tipo de entrega `DELIVERY`/`PICKUP` | Implementado no backend; envio de checkout preparado na branch `feature/checkout-mvp` | 85% estimado | Validar seleção persistida, endereço pertencente ao cliente, endereço do restaurante na retirada e taxa calculada no servidor | `feature/checkout-mvp` |
| P1 | Taxa de entrega por distância | Cálculo backend com validação e snapshot implementado | 85% estimado | Preservar testes e documentar que Haversine é linha reta, não rota do Google Maps | Concluída no backend; ampliar só com escopo de rotas aprovado |
| P1 | Estoque: baixa após pagamento e reposição/cancelamento | Parcial; precisa validar a ligação transacional com pagamento | 75% indicado no backlog original, ainda sem prova de ponta a ponta | Definir e testar idempotência para não baixar/repor duas vezes | `feature/payment-stock-integrity` |
| P1 | Teste de execução Docker integrado | Arquivos `Dockerfile` e `docker-compose.yml` existem; execução final não comprovada | 60% estimado | Subir stack limpa, verificar healthcheck, conectividade frontend/backend, persistência e instruções | `fix/teste-integracao-mvp` |
| P1 | Atualização da documentação de endpoints e documento geral | Prevista para outros membros; status não confirmado no código atualizado | A confirmar | Verificar documentos entregues e acrescentar checkout, segurança e pagamento real que existir | Branch de documentação própria |

## Próximas entregas — até 16/11

| Prioridade | Atividade | Status de partida | Dependência / critério de aceite |
|---|---|---|---|
| P2 | PUSH de novo pedido pelo backend | Não iniciado no planejamento | Escolher canal/provedor, autenticar inscrição e publicar apenas após pedido criado/validado |
| P2 | Receber/exibir PUSH no painel do restaurante | Não iniciado no planejamento | Depende do evento do backend e da autorização de restaurante |
| P2 | PUSH por mudança de status | Não iniciado no planejamento | Evento disparado uma vez por transição confirmada; não duplicar por retries |
| P2 | Acompanhamento do pedido no frontend | Não iniciado no planejamento | Cliente vê somente o pedido próprio e estados coerentes; diferenciar estado comercial e de entrega |
| P2 | Integração de cartão no backend/frontend | Não considerar pronta pela existência de tokenização | Sandbox end-to-end, valor calculado no servidor, retorno e falha tratados sem expor dados de cartão |
| P2 | PayPal: criar/capturar ordem sandbox no checkout | Há tarefa inicial marcada como concluída no planejamento antigo; fluxo de checkout/captura ainda precisa comprovação | Criar e capturar ordem usando valor calculado pelo servidor e verificar idempotência |
| P2 | PIX, Copia e Cola, QR Code e webhook | Não iniciado/integração futura no backlog antigo | Gateway definido, webhook autenticado e confirmação persistida; UI de aguardando pagamento |
| P2 | PDF/NF por e-mail e integração SEFAZ | Não iniciado ou fora do fluxo MVP | Definir regras fiscais e provedor; não apresentar PDF improvisado como NF-e autorizada |
| P2 | Regras e API de recomendação de produtos | Não iniciado | Só depois do catálogo/carrinho estáveis e das regras de negócio aprovadas |
| P3 | Relatórios, aplicativo mobile, leitor de QR/barcode, painel de retirada, redes sociais, AWS/IA | Não iniciado ou fora do fluxo básico | Considerar extras após o caminho principal de compra estar demonstrável e o grupo priorizar |

## Itens prévios mantidos do backlog original

- Cadastro/login por celular e e-mail, códigos de verificação, Google/Facebook, Maps, CRUD de restaurante/produto, listagem de restaurantes/produtos e carrinho possuem implementação no projeto; a validação integrada continua sendo requisito separado.
- A tela de Cardápio do restaurante e a configuração do restaurante foram marcadas como concluídas no planejamento da equipe.
- A tela de Pedidos do Restaurante aparecia como não iniciada no planejamento enviado; confirmar com a responsável antes de assumir que outro trabalho já resolveu isso.
- A demonstração em vídeo foi marcada como concluída no planejamento mais recente enviado.
- O Docker de backend constava como não iniciado no planejamento, mas existem `backend/Dockerfile`, `.dockerignore` e `docker-compose.yml` no repositório; o status correto para acompanhamento deve distinguir arquivos criados de stack validada.

## Atualização de 25/10/2026

O PR #26 (`feature/checkout-mvp`) foi integrado em `dev`. Na validação local foram aprovados os 7 testes de checkout, os 74 testes do backend e o build do frontend. O carrinho envia `restaurant_id`, `order_type`, `payment_method` e itens para `POST /pedidos`; o backend valida preço, estoque, endereço e taxa. O pedido fica `PENDENTE_PAGAMENTO`; nenhuma cobrança é simulada. A validação real pelo navegador permanece pendente.

## Regra de conclusão

Uma tarefa só deve passar para “Concluído” quando tiver: implementação no branch integrado; testes relevantes passando; fluxo de integração validado quando aplicável; documentação atualizada; e confirmação do comportamento no ambiente pretendido. “Existe endpoint” ou “compila” isoladamente não satisfaz esses critérios.


## Atualização de 25/10/2026 — teste de fumaça

Foi adicionada a suíte `backend/tests/integration/test_mvp_smoke.py` para percorrer catálogo público, endereços do cliente, criação/consulta de pedido, modalidades DELIVERY/PICKUP e recusa sem autenticação. O roteiro manual correspondente está em `docs/teste-fumaca-mvp.md`. Até a execução local e a validação do navegador serem registradas, o item permanece em andamento e não é considerado concluído.


## Atualização de 25/10/2026 — fumaça integrada

A branch `fix/teste-integracao-mvp` foi criada a partir de `dev` após o merge do PR #26. O PR #27 foi mesclado em `dev`. A execução local informou 3 testes de fumaça, 77 testes de backend, build do frontend e `git diff --check` aprovados. A validação manual no navegador com ambiente/provedor real continua pendente.


## Atualização de 25/10/2026 — autenticação OAuth

O PR #27 (`fix/teste-integracao-mvp`) foi mesclado em `dev` após a validação local informada: 3 testes de fumaça, 77 testes de backend e build do frontend aprovados. A nova frente `feature/oauth-validation` endurece o callback do Facebook com `state` aleatório vinculado a cookie HttpOnly/SameSite e remove logs que poderiam imprimir claims pessoais de um token Google inválido. Foram preparados testes automatizados com respostas simuladas e um roteiro de configuração. Os testes com credenciais/provedores reais ainda precisam ser executados localmente; OAuth não é marcado como validado por esses mocks.
