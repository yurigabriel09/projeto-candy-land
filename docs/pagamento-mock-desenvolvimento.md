# Pagamento mock — ambiente local e testes

## Objetivo e limite

O adaptador `mock` permite validar o ciclo técnico de pagamento do CandyLand sem credenciais externas. Ele **não fala com PayPal/Mercado Pago, não movimenta dinheiro e não comprova uma integração real**. O uso é bloqueado pelo factory e pela camada de serviço fora de `APP_ENV=development`, `dev`, `local`, `test` ou `testing`.

O `.env.example` mantém `PAYMENT_PROVIDER=none` como padrão seguro. Para executar a simulação local, configure apenas no `.env` de desenvolvimento:

```dotenv
APP_ENV=development
PAYMENT_PROVIDER=mock
```

Não altere `.env` de produção para usar o mock. O frontend não pode definir o valor do pagamento; o backend lê `orders.total` persistido e confirma o estoque usando a rotina transacional idempotente existente.

## Endpoints

Todas as rotas exigem `Authorization: Bearer <JWT>` e pertencem ao cliente dono do pedido.

- `POST /pedidos/{id}/pagamento` cria a tentativa pendente. Aceita `Idempotency-Key` no cabeçalho; o corpo enviado pelo cliente não define valor/moeda. Para a primeira versão, há uma tentativa por pedido e requisições repetidas retornam a já persistida.
- `GET /pedidos/{id}/pagamento` consulta a tentativa do pedido.
- `POST /pedidos/{id}/pagamento/mock-result` simula `{"outcome":"pending"}`, `{"outcome":"rejected"}`, `{"outcome":"approved"}` ou `{"outcome":"cancelled"}`. Esta rota só funciona quando o provedor está configurado como `mock` e o ambiente é explicitamente não produtivo.

Exemplo em PowerShell, com `$token` e `$pedidoId` preenchidos:

```powershell
$headers = @{ Authorization = "Bearer $token"; "Idempotency-Key" = "local-pedido-$pedidoId-pagamento-v1" }
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/pedidos/$pedidoId/pagamento" -Headers $headers

# Simula a resposta do provedor; use approved/rejected/pending/cancelled.
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/pedidos/$pedidoId/pagamento/mock-result" -Headers $headers -ContentType "application/json" -Body '{"outcome":"approved"}'

Invoke-RestMethod -Method Get -Uri "http://localhost:5000/pedidos/$pedidoId/pagamento" -Headers $headers
```

## Persistência e regras

A nova tabela `payment_attempts` armazena apenas campos normalizados: provedor, referência externa, método, valor, moeda, status, detalhes do meio de pagamento e o último evento simulado. `db.create_all()` cria essa tabela nova em bancos existentes; não é necessário alterar ou apagar dados existentes.

A aprovação simulada chama `OrderService.confirmar_pagamento()`. A tentativa, a transição do pedido e a baixa de estoque compartilham a mesma sessão transacional no caminho de sucesso. A chave do evento repetido evita reaplicá-lo; a operação de confirmação também é idempotente. Se o estoque não permitir concluir a confirmação, a transação é revertida e a tentativa fica `ACTION_REQUIRED`, sem baixa parcial.

## Não coberto nesta etapa

Ainda faltam adaptadores de gateway real, captura/API real, credenciais de sandbox, validação criptográfica de webhook do provedor real, histórico completo de eventos, política para múltiplas tentativas após recusa, reembolso real e interface de checkout para apresentar as ações de pagamento. O mock não deve ser descrito como pagamento real nem como webhook de produção validado.
