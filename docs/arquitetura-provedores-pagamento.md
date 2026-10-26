# Arquitetura neutra de provedores de pagamento — CandyLand

**Estado:** contrato comum preservado; adaptador Mercado Pago Checkout Pro adicionado no código local. A integração só é utilizável após configurar o Access Token de teste e validar retorno/Webhook. O adaptador PayPal não está implementado.

## Objetivo

Permitir que o grupo escolha PayPal ou Mercado Pago sem espalhar diferenças do provedor pelo `OrderService`, controllers ou checkout. O código de pedidos deve conversar com um contrato interno comum; cada integração implementa um adaptador que traduz o contrato para a API e os webhooks do provedor.

O adaptador `mercado_pago_adapter.py` cria preferências pela Preferences API e consulta pagamentos reais no endpoint do Mercado Pago. Webhooks usam `x-signature`, consultam o pagamento autenticamente e correlacionam `external_reference` com um pedido CandyLand. O fluxo ainda depende de credenciais e de validação ponta a ponta; não habilite produção antes disso. O adaptador PayPal continua fora do código.

## Conceitos que não devem ser misturados

- **Provedor:** `paypal` ou `mercadopago`. É uma configuração de implantação, não uma forma de pagamento.
- **Meio de pagamento:** `PIX`, `CARTAO_CREDITO`, `CARTAO_DEBITO` ou `BOLETO`. Cada adaptador deve declarar quais meios estão realmente habilitados para as credenciais/conta em uso.
- **Estado interno:** `CREATED`, `PENDING`, `ACTION_REQUIRED`, `APPROVED`, `REJECTED`, `CANCELLED`, `REFUNDED` ou `UNKNOWN`. Os estados externos nunca devem ser copiados cegamente para `orders.status`.

## Contrato comum

`backend/app/services/payment_providers/contracts.py` define:

- `CreatePaymentCommand`: identificador do pedido, chave estável de idempotência, total, moeda, meio e metadados mínimos. O valor deve vir do pedido persistido/calculado pelo backend, nunca de um total fornecido pelo navegador.
- `PaymentResult`: resultado normalizado; links/artefatos de Pix ou boleto são opcionais, de acordo com o método realmente suportado.
- `VerifiedPaymentEvent`: evento normalizado. Só pode ser produzido por um adaptador após a verificação documentada da autenticidade do webhook.
- `PaymentProvider`: interface para criar, capturar, consultar, cancelar, reembolsar e validar webhooks.
- `factory.py`: seleciona o adaptador pelo `PAYMENT_PROVIDER`, sem fallback silencioso para pagamentos falsos. O Mercado Pago usa `MERCADO_PAGO_ACCESS_TOKEN` apenas no backend; webhook usa `MERCADO_PAGO_WEBHOOK_SECRET`.

`mercado_pago_adapter.py` (`MercadoPagoPaymentProvider`) implementa Checkout Pro e é selecionado por `PAYMENT_PROVIDER=mercadopago`. `paypal_adapter.py` (`PayPalPaymentProvider`) continua futuro e não deve ser selecionado. Selecionar o Mercado Pago sem `MERCADO_PAGO_ACCESS_TOKEN` configurado retorna erro explícito.

## Comparação documentada (25/10/2026)

| Critério | PayPal | Mercado Pago |
|---|---|---|
| Cartão | Checkout padrão e opções avançadas de cartão; disponibilidade depende da integração e elegibilidade da conta. | Checkout Transparente/Orders API documenta cartão de crédito. O conjunto exato de meios ativos deve ser consultado na conta. |
| Pix | Há um acordo Pix do PayPal para pessoas jurídicas elegíveis, mediante solicitação e aprovação prévias. Isso não garante acesso automático a uma API de checkout para esta conta. | Checkout Transparente/Orders API documenta Pix por QR Code ou código de pagamento. |
| Boleto | A documentação Braintree de Boleto indica disponibilidade limitada a comerciantes-piloto no Brasil. Não se deve contar com esse meio sem elegibilidade confirmada. | Checkout Transparente/Orders API documenta boleto bancário. |
| Decisão | Confirmar elegibilidade e o produto/API concretos antes de prometer os três meios. | A documentação atual cobre mais diretamente os três meios solicitados no checkout brasileiro. |

Fontes oficiais consultadas:

- Mercado Pago — [Checkout Transparente Orders API](https://www.mercadopago.com.br/developers/pt/reference/online-payments/checkout-api/overview)
- Mercado Pago — [Pix](https://www.mercadopago.com.br/developers/pt/docs/checkout-api-orders/payment-integration/websites/pix)
- Mercado Pago — [Boleto](https://www.mercadopago.com.br/developers/pt/docs/checkout-api-orders/payment-integration/websites/boleto)
- PayPal — [Contrato Pix para pessoas jurídicas elegíveis](https://www.paypal.com/br/legalhub/paypal/pp-pix-agreement?locale.x=pt_BR)
- PayPal/Braintree — [Boleto Bancário (disponibilidade limitada a piloto)](https://developer.paypal.com/braintree/docs/guides/local-payment-methods/boleto-bancario)
- PayPal — [Checkout e métodos de pagamento](https://developer.paypal.com/docs/checkout/apm/)

**Recomendação técnica, não decisão de negócio:** se o requisito obrigatório for oferecer cartão, Pix e boleto no Brasil com menos dependência de uma exceção de elegibilidade, Mercado Pago parece encaixar-se mais diretamente na documentação da API. Como o planejamento atribui a integração PayPal a outra pessoa, esta branch não implementa nem substitui esse trabalho. O grupo precisa decidir o provedor e confirmar as condições da conta antes da integração real.

## Regras obrigatórias para a etapa dos adaptadores

1. Persistir uma tentativa/transação com pedido interno, provedor, identificador externo, valor/moeda, estado normalizado e chave de idempotência, com migração compatível com o banco implantado.
2. Não incluir número completo/CVV do cartão no backend nem nos logs. Usar campos hospedados/tokenização do provedor e seguir a documentação PCI aplicável.
3. Criar/capturar pagamentos apenas no backend, com valor oriundo do pedido persistido.
4. Verificar assinatura/autenticidade do webhook usando a documentação do provedor; não confiar apenas no corpo JSON ou em um `order_id` recebido.
5. Deduplicar eventos por provedor + ID do evento e tolerar eventos repetidos/fora de ordem.
6. Só converter o pedido em `PAGAMENTO_CONFIRMADO` quando a evidência de pagamento liquidado for válida para o meio escolhido. Emitir boleto ou mostrar QR Pix é estado pendente, não pagamento confirmado.
7. Confirmar pagamento e baixa de estoque na transação/idempotência já coberta pelo PR #30. Definir a política de reserva/expiração de estoque para Pix e boleto antes de colocá-los em produção.
8. Testar sucesso, pendência, recusa, cancelamento, reembolso, webhook inválido, evento duplicado e falhas do provedor no sandbox antes de habilitar o fluxo.

## Testes da base

```powershell
cd backend
python.exe -m pytest tests\business_rules\test_payment_provider_contract.py -q
```

Os testes exercitam o contrato, a criação de preferência com resposta simulada e a rejeição de assinatura inválida sem acessar a rede. Eles não comprovam credenciais reais, webhook recebido pela internet ou transações no ambiente de teste.
