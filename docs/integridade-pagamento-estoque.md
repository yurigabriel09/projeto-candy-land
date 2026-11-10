# Integridade transacional de pagamento e estoque — CandyLand

**Objetivo:** impedir que uma confirmação repetida debite estoque de novo e que um cancelamento repetido reponha itens mais de uma vez.

## Implementado na camada de serviço

- `OrderService.confirmar_pagamento()` tenta mover o pedido com UPDATE condicional de `PENDENTE_PAGAMENTO` para `PAGAMENTO_CONFIRMADO`. A mudança de estado e a baixa condicional de estoque são atômicas.
- As quantidades são agrupadas por produto; cada baixa exige que `current_stock` seja suficiente. Falha de um item desfaz todas as atualizações daquela confirmação.
- Reenvio da confirmação de pedido já pago ou em estados posteriores não executa outra baixa. Pedido cancelado retorna conflito.
- Cancelamento do cliente e do restaurante usa o mesmo procedimento transacional: mudança condicional para `CANCELADO`, eventual reposição somente para pedido cujo pagamento já foi confirmado, e cancelamento logístico. Um segundo cancelamento não altera estoque.

## Testes

Arquivo: `backend/tests/business_rules/test_payment_stock_integrity.py`.

```powershell
cd backend
python.exe -m pytest tests\business_rules\test_payment_stock_integrity.py -q
python.exe -m pytest -q
```

## Fora do escopo

Não há confirmação de pagamento pública ou gateway real nesta tarefa. O serviço interno não deve ser exposto a clientes. Antes da cobrança real, escolher o provedor e implementar webhook com verificação de assinatura/autenticidade, idempotência por evento, tratamento de eventos fora de ordem e conciliação/refund. Validar também a concorrência no banco de dados previsto para implantação.
