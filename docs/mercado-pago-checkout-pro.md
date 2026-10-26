# Mercado Pago Checkout Pro — configuração do CandyLand

O CandyLand usa o Checkout Pro: o backend cria uma preferência pela API do Mercado Pago e o navegador é redirecionado para a página segura do provedor. O backend confirma o pagamento consultando a API do Mercado Pago e/ou recebendo um Webhook assinado. O retorno do navegador, sozinho, não confirma pagamento.

## 1. Criar a aplicação

1. Acesse [Mercado Pago Developers](https://www.mercadopago.com.br/developers/panel/app).
2. Clique em **Criar aplicação**.
3. Na lista “Escolha uma solução para integrar”, selecione **Checkout Pro** (não “Assinaturas” nem “Checkout Transparente”).
4. Dê o nome **CandyLand** e finalize a criação.
5. Abra a aplicação criada e escolha o ambiente **Teste** no seletor de ambiente.
6. Entre em **Credenciais** e copie o **Access Token de teste**.

O backend precisa do Access Token. O **Public Key não é necessário para este fluxo Checkout Pro**, porque o frontend não inicializa um formulário de cartão: ele redireciona para `sandbox_init_point` retornado pela API. Nunca coloque o Access Token em `frontend/.env`, em React, no README, em commits ou em mensagens.

Referências oficiais:
- [Criar aplicação e acessar credenciais](https://www.mercadopago.com.br/developers/pt/docs/checkout-pro-orders/create-application?scope=prod)
- [Criar preferência do Checkout Pro](https://www.mercadopago.com.br/developers/pt/reference/online-payments/checkout-pro-preferences/create-preference/post)

## 2. Configurar o backend

Copie `backend/.env.example` para `backend/.env` se ainda não existir e preencha pelo menos:

```dotenv
APP_ENV=development
PAYMENT_PROVIDER=mercadopago
MERCADO_PAGO_ACCESS_TOKEN=COLE_AQUI_O_ACCESS_TOKEN_DE_TESTE
MERCADO_PAGO_SANDBOX=true
MERCADO_PAGO_RETURN_URL_BASE=http://localhost:5173
MERCADO_PAGO_NOTIFICATION_URL=
MERCADO_PAGO_WEBHOOK_SECRET=
```

Mantenha `MERCADO_PAGO_SANDBOX=true` enquanto testa. Reinicie o Flask depois de alterar `.env`. Não altere o `.env` de produção com credenciais de teste.

## 3. Endereço, raio e coordenadas

Para entrega, o restaurante precisa ter endereço comercial ativo com latitude/longitude e `raio_entrega_km` preenchido. Acesse o painel do parceiro em **Config** e salve o raio, a taxa base, a taxa por quilômetro e as coordenadas do endereço comercial.

No carrinho, quando o endereço selecionado ainda não tem coordenadas, o frontend tenta localizá-lo automaticamente usando `GOOGLE_MAPS_GEOCODING_API_KEY` e salva latitude/longitude no backend. Se a chave não estiver configurada ou o endereço não for encontrado, a tela explica o motivo e oferece a opção de informar/obter as coordenadas manualmente. Use a localização atual do computador somente quando você estiver fisicamente no endereço de entrega; caso contrário, ela pode apontar para um lugar errado.

## 4. Webhook para sincronização automática

Para receber notificações locais, exponha o backend por uma URL pública HTTPS (por exemplo, túnel de desenvolvimento). Em Integrações > aplicação CandyLand > Webhooks, selecione **Teste**, configure a URL HTTPS terminando em `/pedidos/webhooks/mercadopago` e copie o segredo de assinatura para `MERCADO_PAGO_WEBHOOK_SECRET`.

Configure também `MERCADO_PAGO_NOTIFICATION_URL` com essa URL HTTPS completa. Reinicie o backend.

Sem um túnel, deixe `MERCADO_PAGO_NOTIFICATION_URL` e `MERCADO_PAGO_WEBHOOK_SECRET` vazios. O retorno do Checkout Pro continuará consultando o pagamento pela API, mas o webhook não chegará ao `localhost`. Notificações `merchant_order` são respondidas com HTTP 200 e ignoradas; elas não aprovam pagamentos. Eventos IPN/legacy sem envelope assinado são reconhecidos sem alterar o pedido; o retorno autenticado consulta o recurso do pagamento diretamente na API. Se um evento moderno `payment` assinado retornar 401, confira se o segredo é exatamente o da aplicação e ambiente escolhidos no painel, sem desativar a verificação da assinatura.

Referência oficial: [Configurar notificações Webhook](https://www.mercadopago.com.br/developers/pt/docs/checkout-pro-preferences/payment-notifications).

## 5. Testar

1. Use uma conta compradora de teste criada pelo Mercado Pago; não use cartão real.
2. Inicie backend e frontend, entre como cliente e selecione um produto.
3. Para **Entrega**, preencha e salve coordenadas do cliente e certifique-se de que a doceria configurou seu raio comercial. Para **Retirada**, não é necessária a taxa de entrega.
4. Clique em **Confirmar pedido e pagar**. O pedido é persistido primeiro; depois o browser abre o Checkout Pro.
5. Conclua uma compra de teste e aguarde a página de retorno consultar o pagamento. O backend só muda para `PAGAMENTO_CONFIRMADO` quando a API do Mercado Pago informar aprovação compatível com o valor/moeda do pedido; a confirmação aciona a regra transacional de estoque existente.
6. Confira o pedido na página **Pedidos** do painel do restaurante.

A integração não deve ser marcada como produção concluída antes de testar retorno, webhook HTTPS, estados pendente/recusado/aprovado, idempotência e autorização em ambiente publicado.


## Geocodificação e mapas de localização

- O mapa incorporado no React usa OpenStreetMap e não exige uma chave de mapa. A atribuição aos colaboradores do OpenStreetMap é exibida abaixo do mapa.
- Para localizar automaticamente um endereço salvo e obter coordenadas para a regra de entrega, configure `GOOGLE_MAPS_GEOCODING_API_KEY` somente no `backend/.env` e habilite a API Geocoding no Google Cloud. Restrinja a chave a essa API e a mantenha no backend.
- Se a chave de geocodificação não estiver configurada ou o Google não encontrar o endereço, o checkout informa a causa e permite informar/obter coordenadas manualmente. Sem coordenadas não é seguro inventar um ponto de entrega.
- O backend persiste as coordenadas no endereço do cliente. Na criação do pedido, o servidor calcula a distância em linha reta com Haversine, calcula a taxa e rejeita destinos fora do raio configurado pelo restaurante. Isso não equivale à rota por ruas.
- A tela de acompanhamento atualiza o estado do pedido periodicamente e mostra o mapa do endereço salvo. Não mostra GPS em tempo real do entregador, pois a integração logística ainda não fornece coordenadas do motorista.
- Sem `MERCADO_PAGO_ACCESS_TOKEN`, o pedido pode ser criado, mas o pagamento permanece pendente e nenhuma cobrança é feita. Configure `PAYMENT_PROVIDER=mercadopago` e o Access Token de teste para testar o Checkout Pro Sandbox.


## Seleção de retirada e cartão

O endpoint público `GET /restaurantes/:id/enderecos/retirada` retorna os endereços ativos da unidade principal e de outras unidades cadastradas. O checkout envia `pickup_address_id`, que o backend valida contra o restaurante. Pedidos ainda `PENDENTE_PAGAMENTO` continuam consultáveis pelo cliente, mas ficam fora da listagem operacional do restaurante.

A opção exibida para cartão é genérica; o backend só registra crédito ou débito após o Mercado Pago informar `payment_type_id` no resultado real. A integração omite `account_money` das exclusões porque o gateway rejeita expressamente sua exclusão; assim, Checkout Pro pode manter opções controladas pelo próprio Mercado Pago, mesmo quando a pessoa seleciona PIX/Cartão no CandyLand.
