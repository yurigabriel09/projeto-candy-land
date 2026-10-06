# Regras de negócio — Pedidos e Entregas

> Documento de referência do fluxo operacional do pedido. Sempre que uma regra de negócio for alterada, este documento deve ser atualizado junto com os testes automatizados e, quando houver impacto físico, com o modelo de dados.

## 1. Estado principal do pedido

O pedido possui um estado principal que representa o ciclo comercial/operacional:

```text
PENDENTE_PAGAMENTO
        ↓
PAGAMENTO_CONFIRMADO
        ↓
RESTAURANTE_RECEBEU
        ↓
RESTAURANTE_ACEITOU
        ↓
PROCESSANDO
        ↓
PRONTO_PARA_ENTREGA
        ↓
ENTREGUE
        ↓
FINALIZADO
```

O pedido também pode ser `CANCELADO` enquanto a regra de negócio permitir o cancelamento.

## 2. Estado da entrega

A logística possui um estado independente do estado principal do pedido. Isso permite que um motorista seja encontrado enquanto a doceria ainda está produzindo.

```text
NAO_SOLICITADO
        ↓
PROCURANDO
        ↓
MOTORISTA_ENCONTRADO
        ↓
MOTORISTA_A_CAMINHO
        ↓
MOTORISTA_NO_RESTAURANTE
        ↓
PEDIDO_RETIRADO
        ↓
EM_ROTA
        ↓
ENTREGA_CONCLUIDA
```

Exceções:

- `MOTORISTA_A_CAMINHO -> PROCURANDO`: motorista cancelou ou ficou indisponível e o sistema deve procurar outro.
- `SEM_MOTORISTA -> PROCURANDO`: nova tentativa de atribuição.
- A busca de motorista pode acontecer em paralelo com `PROCESSANDO`.

## 3. Regras de transição

### Pedido

| Estado atual | Próximos estados permitidos |
|---|---|
| PENDENTE_PAGAMENTO | PAGAMENTO_CONFIRMADO, CANCELADO |
| PAGAMENTO_CONFIRMADO | RESTAURANTE_RECEBEU, CANCELADO |
| RESTAURANTE_RECEBEU | RESTAURANTE_ACEITOU, CANCELADO |
| RESTAURANTE_ACEITOU | PROCESSANDO, CANCELADO |
| PROCESSANDO | PRONTO_PARA_ENTREGA, CANCELADO |
| PRONTO_PARA_ENTREGA | ENTREGUE, CANCELADO |
| ENTREGUE | FINALIZADO |
| FINALIZADO | — |
| CANCELADO | — |

### Entrega

| Estado atual | Próximos estados permitidos |
|---|---|
| NAO_SOLICITADO | PROCURANDO, CANCELADO |
| PROCURANDO | MOTORISTA_ENCONTRADO, SEM_MOTORISTA, CANCELADO |
| MOTORISTA_ENCONTRADO | MOTORISTA_A_CAMINHO, PROCURANDO, CANCELADO |
| MOTORISTA_A_CAMINHO | MOTORISTA_NO_RESTAURANTE, PROCURANDO, CANCELADO |
| MOTORISTA_NO_RESTAURANTE | PEDIDO_RETIRADO, PROCURANDO, CANCELADO |
| PEDIDO_RETIRADO | EM_ROTA, CANCELADO |
| EM_ROTA | ENTREGA_CONCLUIDA, CANCELADO |
| ENTREGA_CONCLUIDA | — |
| SEM_MOTORISTA | PROCURANDO, CANCELADO |
| CANCELADO | — |

## 4. Cancelamentos e eventos

Cancelamento não deve ser tratado apenas como uma troca de texto no campo de status. O sistema deverá registrar o evento e executar as consequências correspondentes.

Exemplo: se o cliente cancelar durante `PROCESSANDO`, o sistema deve interromper o fluxo de produção conforme as regras do projeto, tratar estoque/pagamento quando aplicável e impedir novas etapas de entrega.

Se um motorista cancelar durante a atribuição, o pedido não deve ser cancelado automaticamente: a entrega deve retornar para `PROCURANDO` quando a regra permitir.

## 5. Histórico

As transições relevantes devem ser auditáveis. A implementação completa do histórico deverá registrar, no mínimo, pedido, estado anterior, novo estado, ator/evento, data e observação quando aplicável.

## 7. Pagamento do pedido

Para o fluxo de pedidos do cliente, as modalidades são:

- `PIX`
- `CARTAO_CREDITO`

`MERCADO_PAGO` e `PAYPAL` representam provedores/integradores, não modalidades de pagamento.

A bandeira do cartão não será tratada como uma regra fixa do CandyLand. Quando houver integração real, o provedor deverá informar/validar a bandeira e os meios efetivamente disponíveis. O sistema deve armazenar a modalidade escolhida e, quando aplicável, os metadados retornados pelo provedor.

O pedido permanece em `PENDENTE_PAGAMENTO` até receber uma confirmação válida do provedor. Somente depois da confirmação o pedido pode avançar para `RESTAURANTE_RECEBEU`.

`BOLETO` não faz parte do checkout do pedido do cliente neste escopo. Pode ser reavaliado em uma futura funcionalidade de fornecedor/abastecimento de estoque, caso esse extra seja aprovado pelo grupo.

## 8. Regra de sincronização

Sempre que este fluxo for alterado:

1. atualizar este documento;
2. atualizar os testes de regras de negócio;
3. atualizar o modelo físico em `docs/modelo-dados.md` se houver alteração de estrutura;
4. implementar a mudança;
5. executar a suíte de testes antes do merge em `dev`.
