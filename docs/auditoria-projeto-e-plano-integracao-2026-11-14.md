# Auditoria técnica CandyLand e plano de integração

**Data do retrato:** 14/11/2026  
**Base analisada:** branch `main`, commit `ce72352cd53d0b44263d367a2a3c49d3cbd05bf5`  
**Branch de integração:** `dev`, commit `008606d427c0625605fc29c8099af05645e075b7`  
**Método:** inspeção estática de código, árvore do repositório, branches e diferenças entre refs. Nenhum teste, build, webhook real, gateway de pagamento ou envio FCM foi executado nesta auditoria.

## 1. Resumo executivo

O CandyLand possui uma base funcional significativa: API Flask separada por rotas/controladores/serviços/modelos, frontend React, aplicativo Android Kotlin, adaptadores de pagamento, autenticação social, cálculo de entrega, histórico de pedidos e estrutura inicial de push notifications.

**Veredito: MVP tecnicamente estruturado, mas ainda não pronto para produção ou cobrança real.** O principal bloqueio é o ciclo de vida pedido-pagamento-estoque: a criação do pedido e a confirmação do pagamento estão com estados incompatíveis. Esse defeito pode impedir a abertura de uma tentativa de pagamento e, em cenários de cancelamento, causar divergência de estoque. A jornada web também pode apresentar sucesso sem iniciar de fato o provedor de pagamento.

A primeira correção deve tratar o contrato de pedido e pagamento de ponta a ponta, compartilhado por web e Android. Não se deve polir telas ou ativar cobrança real antes de corrigir e testar esse fluxo.

## 2. Branches e sincronização

- O repositório possui **34 branches** no retrato atual.
- `main` é a branch padrão.
- `main` está **3 commits à frente de `dev`**. A comparação `dev...main` apontou uma alteração de código no adaptador PayPal (`backend/app/services/payment_providers/paypal_adapter.py`, +26/-14), além dos commits de merge que trouxeram a integração.
- A correção PayPal mais recente está em `main`, mas ainda não chegou a `dev`.
- Por isso, a branch desta documentação deve nascer de `main`, e o PR deve ter `dev` como destino. Isso mantém o fluxo de revisão acordado e evita reintroduzir uma versão desatualizada do adaptador.
- O histórico inclui várias branches antigas de funcionalidades; não fazer merge em lote. Comparar cada branch com a base atual antes de aproveitar commits.
- No retrato anterior, `feature/restaurant-configuration` tinha um commit exclusivo que alterava `ALLOW_DUPLICATE_PHONE` no `.env.example`; revisar a decisão de negócio antes de recuperar qualquer conteúdo dessa branch.
- A conexão GitHub usada nesta sessão recusou a criação remota de referência com HTTP 403. Por isso, o pacote de aplicação cria a branch localmente a partir de `origin/main`; o push é uma etapa explícita do usuário.

## 3. Bloqueio P0 — pedido, pagamento e estoque

### Evidência de implementação

1. `OrderService.criar_pedido` cria o pedido com status `PAGAMENTO_CONFIRMADO`.
2. `PaymentService.criar_pagamento` só permite iniciar tentativa quando o pedido está `PENDENTE_PAGAMENTO`.
3. O fluxo Android cria o pedido e depois chama a inicialização do pagamento; com o estado acima, o backend pode rejeitar a tentativa.
4. O checkout web faz POST do pedido, adapta o identificador PayPal para `CARTAO_CREDITO`, não inicia o pagamento pelo serviço unificado e pode limpar o carrinho/mostrar sucesso sem confirmação do provedor.
5. A confirmação de pagamento é o ponto em que o estoque é decrementado de forma transacional. Se o pedido já nasce confirmado, o decremento pode ser ignorado como confirmação duplicada.
6. A lógica de cancelamento pode restaurar estoque para pedidos cujo status não é pendente; se o estoque nunca foi debitado na confirmação, a restauração pode aumentar artificialmente o saldo.
7. Testes de smoke existentes esperam que a criação do pedido retorne `PENDENTE_PAGAMENTO`, portanto há divergência entre contrato testado e implementação.

### Fluxo-alvo

`carrinho -> criar pedido PENDENTE_PAGAMENTO -> criar tentativa no provedor -> aguardar confirmação verificável -> confirmar pagamento de modo idempotente -> debitar/reservar estoque conforme política -> notificar restaurante -> permitir andamento/retirada/entrega`.

Apenas retorno do frontend, redirecionamento ou clique do usuário não deve confirmar pagamento. A confirmação deve vir de resposta autenticada/validada do provedor (webhook e/ou consulta server-to-server), com idempotência.

### Decisão de negócio que precisa ser formalizada

Escolher como impedir venda acima do estoque durante o intervalo em que o pagamento está pendente:

- **Reserva temporária:** reservar unidades ao criar a tentativa; liberar em recusa/expiração/cancelamento; converter reserva em baixa definitiva após confirmação.
- **Baixa somente após pagamento:** menor complexidade inicial, mas existe risco de pagamento aprovado sem estoque quando pedidos concorrentes disputam as últimas unidades.

A escolha deve definir prazo de reserva, expiração, reprocessamento e estorno.

## 4. Estado dos 17 itens acompanhados

| # | Item | Situação observada | Próxima ação |
|---:|---|---|---|
| 1 | Previsão de entrega (ETA) | Campo de estimativa existe, mas não foi identificada atribuição consistente no fluxo auditado. | Definir regra com preparo + deslocamento e preencher no backend. |
| 2 | Dados que devem sair do histórico/checkout | O material de referência em vídeo não estava anexado nesta sessão; não há base para decidir exatamente quais campos ocultar. | Comparar vídeo/tela atual e registrar decisão antes de remover dados. |
| 3 | Carrinho após criar pedido | O carrinho é limpo em caminhos do web e Android, mas o web não confirma pagamento corretamente. | Limpar após persistência válida do pedido; preservar pendência e permitir retomar pagamento. |
| 4 | Acompanhamento do pedido | Rota/tela de tracking existe e faz polling; mapa indica limitação de GPS do entregador e usa distância em linha reta. | Validar a navegação após corrigir pagamento e definir origem confiável do status. |
| 5 | Notificação ao restaurante | Há serviço e chamada de notificação, mas a criação atual pode notificar antes da confirmação real. | Notificar após confirmação válida; testar em dispositivo e tratar falhas/retries. |
| 6 | Polimento do frontend | Há telas completas e trechos que exigem revisão de consistência/feedback. | Tratar após estabilizar contrato de pedido/pagamento. |
| 7 | Histórico de compras | Tela de histórico existe e consome pedidos persistidos. | Confirmar estados, valores e links depois do novo ciclo de checkout. |
| 8 | Integração dos meios de pagamento | Adaptadores PayPal e Mercado Pago existem; a integração do checkout web não segue o fluxo unificado. | Fazer web e Android usarem o mesmo contrato backend; remover mapeamentos enganosos. |
| 9 | Quantidade no carrinho | Controles +/- existem, mas limites e sincronização com estoque precisam reforço. | Impor limites na UI e validar novamente no backend. |
| 10 | Pix | Adaptador e retorno Pix/copia e cola existem; dependem do fluxo correto de pedido pendente. | Testar criação, QR/copia e cola, expiração, webhook e retry. |
| 11 | Segurança do estoque | Há decremento condicional e transacional em confirmação, mas o status inicial contradiz o fluxo e há lacunas de disponibilidade concorrente. | Corrigir o ciclo e testar concorrência, cancelamento, duplicidade e indisponibilidade. |
| 12 | Produtos indisponíveis e favoritos | API expõe disponibilidade; há botão em tela que precisa respeitar o estado. Favoritos não possuem persistência/API completa. | Desabilitar inclusão de indisponível; planejar favoritos como funcionalidade separada. |
| 13 | Avaliações | Tela de avaliações é placeholder; não foi identificada entidade/API persistente. | Criar modelo/API após compra concluída, com uma avaliação por pedido e autorização. |
| 14 | Link “Doces” | O cabeçalho possui link para `/itens`. | Decidir rótulo/visibilidade e ajustar navegação sem quebrar rotas existentes. |
| 15 | Taxa de entrega por distância | Cálculo Haversine, taxa base + por km, raio e retirada sem taxa já existem e têm testes. É distância em linha reta. | Não reescrever sem necessidade; validar resposta/valor exibido antes do pagamento. |
| 16 | Push mobile | Cadastro de token e serviço FCM HTTP v1 existem; credenciais e envio real dependem de configuração externa. | Validar service account, token real, mudanças de status e tratamento de falha. |
| 17 | Login/cadastro mobile | Código para tela inicial, canal email ou telefone e OAuth Google/Facebook está presente. | Validar credenciais reais, deep link, sessão e roteamento de perfil em aparelho. |

## 5. Backend — observações

- `OrderService` concentra criação, validação, taxa, serialização, cancelamento e atualização de pedidos. Deve ser a fonte da regra de estado, sem duplicar decisões no frontend.
- `PaymentService` orquestra adaptadores, idempotência, consulta e webhooks. O provedor precisa ser confirmado server-side.
- `payment_providers/` separa contratos e adaptadores PayPal, Mercado Pago e mock.
- Há testes de integridade de estoque, fluxo de pagamento, taxa, geocoding, autenticação, autorização e notificações. A existência dos testes não prova execução/passe nesta sessão.
- O cadastro de token FCM tem cobertura de API, mas não substitui teste de envio real.

## 6. Frontend web — observações

- `Checkout.jsx` deve parar de inferir pagamento concluído a partir da criação do pedido.
- A UI não deve solicitar nem manter número completo/CVV de cartão se o backend/provedor usa checkout hospedado; preferir redirecionamento/tokenização segura no provedor.
- O total apresentado precisa incluir taxa autoritativa calculada pelo servidor antes da autorização do pagamento.
- Produto indisponível deve ter botão de adicionar desabilitado; o backend continua sendo a validação final.
- Histórico e tracking já existem; validar transições de estado e navegação real após corrigir a API.

## 7. Android — observações

- O pacote `com.candyland.mobile` contém a implementação atual: Activity, API, sessão, modelos, FCM e UI principal.
- O pacote `com.example.candyland` contém implementação antiga/demo. Não foi removido nesta etapa; antes de excluí-lo, validar referências no Manifest, build, testes e navegação.
- Google/Facebook e FCM exigem credenciais/configuração externa e teste em dispositivo real.

## 8. Documentação, segurança e automação

- O README principal contém trechos de escopo/backlog que não refletem mais o código (por exemplo, aplicativo Android, push e tracking).
- Existem capturas de tela em `docs/Credenciais/`. A auditoria textual não consegue atestar se os valores sensíveis estão mascarados nas imagens. Revisar visualmente e revogar/rotacionar qualquer chave exposta.
- Não foram encontrados workflows de CI na árvore auditada e as branches consultadas estavam sem proteção obrigatória. Recomenda-se adicionar pipeline para pytest, build web e build/test Android e exigir checks em PR.
- `backend/app/controllers/controllers/` é pasta duplicada e órfã: as rotas importam os módulos do diretório pai (`app.controllers.*`), nunca do subdiretório repetido. Cinco arquivos são cópias byte a byte; `auth_controller.py` e `payment_controller.py` são versões antigas/diferentes, mas também não são importadas. A remoção é registrada separadamente e limitada a essa pasta.

## 9. Plano de integração em etapas

### Etapa 0 — documentação e alinhamento de branches

- Criar branch documental sobre o `main` atual.
- Registrar arquitetura, pendências, critérios de aceite e arquivos por pasta.
- Remover apenas a pasta duplicada de controladores.
- Abrir PR para `dev`, sincronizando também os três commits que `main` possui a mais.

### Etapa 1 — `fix/checkout-payment-lifecycle` (primeira correção funcional)

1. Fazer criação de pedido sempre iniciar em `PENDENTE_PAGAMENTO`.
2. Garantir que o checkout web inicie tentativa no provedor certo, sem converter PayPal em cartão.
3. Fazer web e Android consumirem contrato uniforme de criação, tentativa, consulta e confirmação.
4. Confirmar pagamento apenas por resultado validado do provedor.
5. Preservar pedido pendente, permitir retry e limpar carrinho somente após pedido persistido.
6. Não notificar restaurante antes da confirmação válida.
7. Corrigir testes de regressão e cobrir PayPal, Mercado Pago/Pix e mock.

**Aceite mínimo:** pedido novo fica pendente; tentativa de pagamento é criada; pagamento não confirmado não libera preparo nem aparece como pago; webhook/consulta confirmado muda estado uma vez; repetição do webhook não duplica efeitos; falha permite retry; web e Android mostram o mesmo estado.

### Etapa 2 — `fix/stock-availability-integrity`

- Formalizar reserva ou baixa tardia.
- Revalidar produto ativo e estoque na confirmação.
- Fazer cancelamento/expiração liberar apenas reserva realmente feita.
- Garantir limites de quantidade no carrinho e validação concorrente no backend.

**Aceite mínimo:** duas compras concorrentes não vendem além do estoque; produto desativado não é confirmado; cancelar não aumenta estoque indevidamente; repetição da confirmação é idempotente.

### Etapa 3 — `feat/delivery-estimate-push`

- Definir ETA e atualizar em eventos relevantes.
- Garantir taxa final autoritativa e visível antes do pagamento.
- Disparar FCM para perfil correto apenas após evento válido, com logs e política de retry.
- Validar tracking e notificações em aparelhos reais.

### Etapa 4 — `fix/customer-purchase-experience`

- Revisar carrinho, histórico, checkout, tracking, navegação e textos.
- Validar o item visual do vídeo quando ele estiver disponível.
- Ajustar link “Doces” sem apagar endpoint necessário.

### Etapa 5 — `feat/favorites-post-purchase-reviews`

- Criar favoritos persistidos e API.
- Criar avaliação associada a pedido concluído, com autorização e prevenção de duplicidade.

### Etapa 6 — `test/mobile-release-readiness`

- Validar Google/Facebook, sessão, deep link, FCM e permissões.
- Limpar código legado somente com prova de não uso.
- Atualizar README/guia de execução, CI e proteção de branches.

## 10. Regras para os próximos PRs

- Uma etapa/objetivo por branch.
- Branch criada da base atualizada; nunca começar de branch antiga sem comparar.
- PR com resumo, arquivos, comportamento esperado, testes executados e riscos.
- Não mesclar para `dev` até o usuário testar e aprovar.
- Não usar credenciais reais em commits; usar `.env.example` sem segredo.
- Registrar alterações de contrato em documentação e testes.
