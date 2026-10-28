# Pagamentos CandyLand — Pix, PayPal e Mercado Pago

## O que esta implementação oferece

- **Pix:** pagamento criado via Mercado Pago Payments API; o backend persiste o identificador, status, QR Code e código Copia e Cola. O frontend apresenta o QR e consulta o status.
- **PayPal:** cria uma ordem PayPal Orders v2, redireciona para aprovação e captura no backend ao retornar ao checkout. A captura usa o ID persistido e chave de idempotência; não usa o retorno do navegador como prova de pagamento.
- **Mercado Pago:** mantém Checkout Pro para a opção Mercado Pago (checkout com cartão), incluindo consulta da API e o webhook assinado já existente.
- **Valor autoritativo:** sempre vem de `orders.total` calculado pelo backend; o frontend não envia nem escolhe o valor cobrado.
- **Estoque:** só é atualizado pela rotina transacional existente após um resultado aprovado e validado.

## Variáveis do backend

Nunca coloque estes segredos no frontend ou em commits. Use credenciais de teste primeiro:

```dotenv
PAYMENT_PROVIDER=auto
FRONTEND_URL=http://localhost:5173

MERCADO_PAGO_ACCESS_TOKEN=SEU_ACCESS_TOKEN_DE_TESTE
MERCADO_PAGO_SANDBOX=true
MERCADO_PAGO_WEBHOOK_SECRET=SEGREDO_DO_WEBHOOK_SE_CONFIGURADO
MERCADO_PAGO_NOTIFICATION_URL=https://SEU_TUNEL_HTTPS/pedidos/webhooks/mercadopago

PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=SEU_CLIENT_ID_SANDBOX
PAYPAL_CLIENT_SECRET=SEU_SECRET_SANDBOX
PAYPAL_API_BASE=https://api-m.sandbox.paypal.com
PAYPAL_RETURN_URL_BASE=http://localhost:5173
PAYPAL_WEBHOOK_ID=ID_DO_WEBHOOK_PAYPAL
```

No PayPal Developer Dashboard, cadastre o webhook HTTPS do backend em `/pedidos/webhooks/paypal` e informe o Webhook ID. Para Mercado Pago, configure a URL HTTPS `/pedidos/webhooks/mercadopago` e seu segredo de assinatura. Em desenvolvimento local, use um túnel HTTPS para webhooks; não exponha credenciais no React.

## Endpoints envolvidos

- `POST /pedidos` cria o pedido com `payment_method`: `PIX`, `PAYPAL` ou `MERCADO_PAGO`.
- `POST /pedidos/{id}/pagamento` cria a cobrança/sessão usando o método persistido no pedido.
- `GET /pedidos/{id}/pagamento` consulta status do pagamento.
- `POST /pedidos/{id}/pagamento/paypal-capture` captura a ordem PayPal após retorno; exige JWT do dono do pedido e confere o token de retorno com a ordem persistida.
- `POST /pedidos/{id}/pagamento/paypal-cancel` registra o retorno pelo caminho de cancelamento do PayPal sem capturar fundos e permite iniciar nova ordem depois.
- `POST /pedidos/webhooks/mercadopago` valida assinatura Mercado Pago e consulta o pagamento na API oficial.
- `POST /pedidos/webhooks/paypal` verifica o evento com a API de verificação de assinatura PayPal antes de processá-lo.

## Testar

```powershell
cd backend
python.exe -m pytest tests\business_rules\test_paypal_adapter.py tests\business_rules\test_mercadopago_pix.py tests\business_rules\test_payment_provider_dispatch.py tests\business_rules\test_payment_provider_contract.py tests\business_rules\test_payment_mock_flow.py tests\business_rules\test_order_service_validation.py -q
python.exe -m pytest -q
cd ..\frontend
npm run build
cd ..
git diff --check
```

Os testes de adapter simulam as respostas HTTP; eles não substituem um teste real com contas e credenciais sandbox. O teste sandbox requer criar usuários compradores de teste nos painéis PayPal/Mercado Pago e validar aprovação, recusa, retorno e webhook por HTTPS.

## Restrições conhecidas

- O banco permite uma tentativa por pedido. Fluxo completo de múltiplas tentativas concorrentes, conciliação financeira/ledger e reembolso operacional ainda requerem revisão própria.
- Não armazene dados de cartão. Mercado Pago Checkout Pro coleta os dados em página segura do provedor; PayPal mantém a aprovação em seu checkout.
- Pix só é considerado pago quando a API/webhook autenticado informar aprovação. Abrir o QR ou voltar à página não confirma o pedido.
