# CandyLand — Plano de entregas priorizado

**Revisão:** 25/10/2026
**Fonte de código:** repositório `yurigabriel09/projeto-candy-land`, branch remota `dev`
**Estado Git conferido:** `dev` = `f67a997`; `main` = `0db9316`. `dev` está 4 commits à frente e 0 atrás de `main`.

> Este plano separa “código existente” de “fluxo validado de ponta a ponta”. Uma rota, tela ou serviço isolado não significa que a funcionalidade esteja pronta para apresentação ou produção.

## 1. Entregas recentes confirmadas

| Entrega | Estado | Evidência / observação |
|---|---|---|
| Resolver conta pela identidade/e-mail e permitir telefone compartilhado só em desenvolvimento/testes quando configurado | Concluída e integrada em `dev` | PR #23 mesclado. Testes locais reportados: 12 específicos de autenticação e 43 no backend antes da etapa de segurança. |
| Proteção de endpoints e autorização por conta | Concluída e integrada em `dev` | PR #25 mesclado. Testes locais reportados: 24 específicos de segurança e 67 no backend completo. |
| CRUD e regras centrais de pedidos | Parcialmente entregues no backend | O serviço, as rotas e a máquina de estados existem. Ainda falta validar o fluxo completo com o frontend/carrinho. |
| Modalidade `DELIVERY`/`PICKUP` | Backend implementado; integração enviada no patch de `feature/checkout-mvp` | O backend valida modalidade/endereço e calcula a taxa; o carrinho agora envia a seleção no pedido. Testes locais e PR ainda pendentes. |
| Taxa de entrega por distância | Cálculo backend implementado | O backend usa Haversine (distância em linha reta), valida raio/coordenadas e grava snapshot da taxa/distância. Não é cálculo de rota por ruas do Google Maps. |
| Modelo físico do banco | Diagrama atualizado em PR #23 | O relacionamento pedido-produto é resolvido por `order_items`, entidade associativa com quantidade/preço/personalização; não há relação N:N direta declarada que precise ser eliminada agora. |

## 2. Objetivo imediato: MVP comprável

A próxima tarefa é fechar um caminho testável do carrinho até um pedido persistido como `PENDENTE_PAGAMENTO`, sem fingir que o pagamento foi concluído.

### Branch

`feature/checkout-mvp` — deve nascer da `dev` atualizada e ser enviada via PR para `dev`.

### Critérios de aceite do checkout

1. Exigir cliente autenticado; conta de restaurante não pode finalizar compra.
2. Recusar carrinho vazio, restaurante ausente, quantidades inválidas e produtos indisponíveis/incompatíveis com o restaurante.
3. Enviar ao backend somente IDs/quantidades/seleção necessários. Recalcular preço, subtotal e total no servidor; não confiar em preço ou taxa enviados pelo navegador.
4. Para `DELIVERY`, aceitar somente endereço ativo pertencente ao cliente autenticado e deixar o backend aplicar regra de coordenadas/raio/taxa já implementada.
5. Para `PICKUP`, resolver o endereço ativo do restaurante no servidor e manter a taxa de entrega em zero.
6. Criar pedido em `PENDENTE_PAGAMENTO`; não baixar estoque definitivamente nem marcar pagamento como confirmado sem um evento de pagamento válido.
7. Exibir erro de validação de forma útil, impedir duplo envio e limpar o carrinho apenas após criação confirmada do pedido.
8. Adicionar testes da API para entrega/retirada, endereço alheio/inativo, preço adulterado, carrinho inválido, usuário sem token e conta BUSINESS.
9. Testar o caminho por HTTP com o frontend, não apenas chamar serviços diretamente.

## 3. Sequência até a entrega do MVP

| Ordem | Atividade | Branch sugerida | Prioridade | Critério para encerrar |
|---:|---|---|---|---|
| 1 | Checkout mínimo: integrar carrinho, API, endereço e `DELIVERY`/`PICKUP` | `feature/checkout-mvp` | P0 | Cliente consegue criar pedido pendente e recebe confirmação/erro visível; testes passam. |
| 2 | Teste de fumaça integrado do MVP | `fix/teste-integracao-mvp` | P0 | Cenário login → catálogo → carrinho → checkout → pedido consultável executado no ambiente local/Compose. |
| 3 | Validar Google OAuth no ambiente local | `feature/google-oauth-validation` | P1 | Client ID correto por ambiente, callback/origin validados, token verificado no backend, sem credenciais no Git. |
| 4 | Validar Facebook OAuth e callback | `feature/facebook-oauth-validation` | P1 | Permissões, redirect URI, URL de frontend e tratamento de cancelamento/erro testados. |
| 5 | Pagamento e estoque idempotentes | `feature/payment-stock-integrity` | P1 | Confirmação do gateway autenticada e idempotente; baixa de estoque uma única vez; cancelamento/reembolso com regra explícita. |
| 6 | PUSH de novo pedido e atualização de estado | `feature/order-notifications` | P2 | Evento criado após transição confirmada e recebido/exibido pelo painel. |
| 7 | Tela de acompanhamento da entrega | `feature/order-tracking-ui` | P2 | Cliente consulta estado comercial e logístico atual do próprio pedido. |
| 8 | Cartão/PayPal/PIX e webhook de pagamento | branches separadas por provedor | P2 | Sandbox de ponta a ponta, cálculo de valor exclusivamente no servidor, webhook verificado e eventos duplicados seguros. |
| 9 | Relatórios, recomendação, mobile, NF-e/PDF e QR/barcode | branches próprias | P3/Extras | Só após checkout e smoke test estáveis e após acordo do grupo sobre escopo. |

## 4. Prazo e estratégia de escopo

A data original das primeiras entregas prioritárias é **segunda-feira, 26/10/2026** (amanhã, considerando a revisão de 25/10). O escopo é apertado; por isso, priorizar checkout mínimo + teste de fumaça + validação prática de OAuth. Push, relatórios, app mobile, recomendação e emissão fiscal devem ser classificados como extras/etapas seguintes caso não caibam sem comprometer o fluxo central.

## 5. Git: política de trabalho

1. Antes de iniciar cada assunto, `git fetch origin`, entrar em `dev` e executar `git pull --ff-only origin dev`.
2. Criar uma branch temática a partir de `dev` atualizado.
3. Não desenvolver diretamente em `dev` ou `main`, não usar `push --force` e não apagar branches com trabalho não integrado.
4. Commits pequenos por assunto; executar testes e `git diff --check`.
5. Abrir PR para `dev`, revisar e mesclar. Só atualizar `main` em uma entrega planejada da equipe.
6. Após o merge, atualizar a `dev` local antes de abrir a próxima branch.

## 6. Pendências técnicas a não declarar como concluídas

- O patch de checkout em `feature/checkout-mvp` habilita o envio do carrinho ao `POST /pedidos`, lista endereços ativos do próprio cliente e mostra a confirmação do pedido pendente. Ainda precisa ser testado na máquina local e integrado por PR.
- O pagamento real continua fora desta etapa: `PIX`/cartão representam a preferência registrada, sem cobrança ou confirmação de gateway.
- O cálculo Haversine é distância em linha reta, não rota rodoviária.
- Estoque e pagamento precisam de fluxo idempotente, com testes que comprovem baixa após confirmação e tratamento de cancelamento.
- Google/Facebook OAuth têm implementações no código, mas a validação local/produção ainda é uma atividade explícita do backlog.
- Dockerfile/Compose existem no repositório; isso não substitui um teste de inicialização integrado e documentado.
- Não há N:N direta entre pedidos e produtos: `order_items` é a entidade associativa necessária e armazena dados próprios da compra.
- A documentação e os diagramas devem ser atualizados junto de qualquer mudança de modelo físico; não apagar banco para contornar divergências.
