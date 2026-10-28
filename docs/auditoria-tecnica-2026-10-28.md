# CandyLand — auditoria técnica completa (28/10/2026)

## Escopo e confiabilidade

Revisão estática da árvore GitHub, dos arquivos de backend/frontend, dos testes, do README, da documentação de pagamentos e das branches publicadas. A branch funcional mais recente é `feature/paypal-mercadopago-pix` (`6dabbaec2603c37c4595672d49dbac7fad577bcb`), com dois commits que ainda não existem em `dev`. O pacote de correção foi preparado para aplicar sobre essa branch, preservando o trabalho de pagamento e histórico que acabara de ser publicado.

**Limitação desta entrega:** o ambiente permitiu leitura do GitHub, mas não baixar o arquivo binário completo nem criar branch/commit remoto. Portanto, não rodei a suíte nem o build contra um checkout local do repositório. O script deste pacote faz isso no checkout do usuário e gera o ZIP integral corrigido localmente. Não declarar os testes aprovados antes de o script apresentar esse resultado.

## Veredito

O projeto está num estágio de MVP web avançado, mas não deve ser tratado como pronto para produção até validar end-to-end as compras, os dois provedores reais, webhooks, autorização, endereços e operacionalização do restaurante. A branch mais nova adicionou PayPal e histórico de compras, mas ela ainda não foi integrada em `dev`: não existia PR aberto quando esta auditoria foi feita.

## Correções incluídas no pacote

1. Configuração do restaurante consulta o ViaCEP ao digitar os oito dígitos, preenche logradouro/bairro/cidade/UF, mostra estados de carregamento/erro e evita respostas assíncronas antigas sobrescreverem edição manual.
2. Se a sessão não contiver um ID empresarial válido, a tela de configuração sai do estado infinito de carregamento e informa o problema.
3. `restaurantService.js`, `productService.js` e `categoryService.js` usam `VITE_API_URL` em vez de misturar hosts fixos `127.0.0.1` e `localhost`.
4. O backend recupera endereço comercial legado vinculado por `id_restaurante` mesmo quando `restaurants.address_id` está vazio; ao criar um novo endereço de configuração, preenche e valida campos obrigatórios antes de enviar `flush` ao banco.
5. A tela de coordenadas mostra o mapa que já existe no projeto quando houver latitude/longitude. O mapa continua sendo prévia, não marcador arrastável.
6. CORS passa a usar a origem configurada em `FRONTEND_URL`, e `run.py` deixa de ativar `debug=True` indiscriminadamente.
7. O botão abrir/fechar no painel deixa de mudar somente o estado visual. O pacote adiciona endpoint autenticado de status, restringe o parceiro a `ABERTO`/`FECHADO`, impede que parceiro aprove ou suspenda a própria loja, e inclui testes de autorização/status.
8. O `.env.example` deixa campos de webhook vazios até o usuário cadastrar endpoint/segredo reais. Na configuração local, o URL de retorno do Mercado Pago usa `http://localhost:5173`; produção/homologação deve substituir pelo frontend publicado.

## Achados adicionais por prioridade

### P0 — antes de produção

- **Segredo JWT fallback:** `backend/app/config/config.py` define um valor conhecido se `SECRET_KEY` estiver ausente. A implantação deve falhar com mensagem explícita quando estiver em produção sem segredo forte. Esse endurecimento exige executar a suíte do projeto/CI para não quebrar ambientes de teste; fica como pendência alta, não como correção já validada neste pacote.
- **Gateway real exige teste sandbox ponta a ponta:** o código de PayPal e Mercado Pago existe na branch `feature/paypal-mercadopago-pix`, mas presença do adaptador não prova que credenciais, URLs de retorno, webhook, captura e reconciliação funcionam com contas reais. Validar Pix, PayPal, Mercado Pago, falhas, cancelamento, repetição de webhook e retorno do navegador.
- **Webhook:** não preencher `MERCADO_PAGO_NOTIFICATION_URL`, `MERCADO_PAGO_WEBHOOK_SECRET` ou `PAYPAL_WEBHOOK_ID` com textos de exemplo. Deixar vazios até existir endpoint HTTPS público e webhook criado no painel do gateway.
- **Autorização operacional:** o novo endpoint de status só autoriza o dono do restaurante, mas precisa de revisão/teste conjunto no checkout e no painel após aplicação.

### P1 — fluxo web e qualidade

- A configuração do restaurante, o status operacional e o catálogo precisam de testes com conta empresarial real, incluindo um restaurante novo e um registro legado com endereço sem `address_id`.
- O código `Itens.jsx` consultado **já chama `adicionarItem`**. A afirmação antiga do README de que esse botão não chama o carrinho está desatualizada e deve ser removida após validar o fluxo no navegador.
- Padronizar a URL da API em todos os serviços frontend; o pacote corrige as URLs fixas encontradas em configuração, produtos e categorias. Conferir ainda chamadas diretas feitas dentro das páginas.
- Documentação de pagamentos anterior a 28/10 afirma que PayPal não está implementado. Isso era verdadeiro em `dev`, mas ficou desatualizado na branch de pagamentos que adicionou `paypal_adapter.py`, rotas de captura/cancelamento/webhook, testes e histórico de compra. Os adendos do script tornam essa diferença explícita, sem declarar o gateway pronto para produção.
- Não há evidência no repositório de testes unitários frontend: `frontend/package.json` oferece dev/build/preview. O build valida compilação, não substitui teste de interface.

### P2 — planejado, não existente

- O repositório não contém projeto Android/Kotlin, arquivos Gradle ou módulo `mobile`. O aplicativo ainda precisa ser criado.
- A notificação push não está completa: o ícone de notificações no painel está desabilitado e não há fluxo fim a fim de registro de dispositivo, envio e recebimento por FCM. Criar a infraestrutura backend, associar token de dispositivo à conta/restaurante, integrar Firebase Cloud Messaging no Android Kotlin e validar novos pedidos/mudanças de status.
- O mapa atual é uma prévia OpenStreetMap com coordenadas informadas manualmente/por localização do navegador. Não há marcador arrastável nem integração comprovada com Google Maps JavaScript na tela de configuração.

## Pagamentos: esclarecimento sobre `PAYMENT_PROVIDER`

Na branch mais recente, o carrinho diferencia `PIX`, `PAYPAL` e `MERCADO_PAGO`; o backend valida `payment_method` no pedido e mapeia `PIX` para Mercado Pago, `PAYPAL` para PayPal e `MERCADO_PAGO` para Mercado Pago. Nesse fluxo, `PAYMENT_PROVIDER=auto` é intencional como modo de despacho/default de cartão. Não remover sem refatorar a seleção. O backend deve continuar escolhendo o adaptador e validando a seleção; não confiar em preço ou status de pagamento fornecidos pelo frontend.

## Documentos que precisam continuar sincronizados

- `README.md`: resumo anterior diz que o PayPal não existe; passa a existir na branch de pagamentos, ainda pendente de PR/teste sandbox.
- `docs/arquitetura-provedores-pagamento.md`: atualizar o estado do adaptador PayPal.
- `docs/mercado-pago-checkout-pro.md`: refletir os defaults locais e manter webhooks vazios até haver URL HTTPS/segredo.
- `docs/Backlog_Funcionalidades_CandyLand_Atualizado_2026-10-25 (2).md`: acrescentar o delta de 28/10; não reescrever contagem de testes como aprovada sem execução.
- `docs/requisitos.md`: registrar a regra operacional de status (só abrir/fechar depois da liberação administrativa).
- `docs/modelo-dados.*`: não precisa mudar para o endpoint de status, pois ele reutiliza a coluna `restaurants.status`; atualizar esses arquivos apenas quando mudar schema.

O script inclui esses adendos nos documentos existentes e adiciona os relatórios de branches/limpeza em `docs/`.

## Sequência de entrega recomendada

1. Extrair este pacote; executar `Aplicar_Correcoes_e_Gerar_Zip.ps1` sobre um clone limpo da branch `feature/paypal-mercadopago-pix`.
2. Conferir a saída do `pytest`, `npm ci`, `npm run build` e `git diff --check`. Se algum teste falhar, não marcar o MVP como validado.
3. Fazer revisão humana do diff, corrigir falhas e só depois publicar a branch `fix/restaurant-config-cep` e abrir PR para `dev`.
4. Após aceite e merge em `dev`, agendar a integração `dev` → `main` segundo o fluxo da equipe.
5. Começar o push e o app Kotlin como fases próprias, usando API/contratos de pedido já testados.
