# Regras de negócio — Pedidos e Entregas

> Documento de referência do fluxo operacional do pedido. Sempre que uma regra de negócio for alterada, este documento deve ser atualizado junto com os testes automatizados e, quando houver impacto físico, com o modelo de dados.

## Modalidade do pedido: entrega ou retirada

A modalidade é enviada no campo `order_type` e deve ser uma das opções:

| Valor da API | Experiência do cliente | Endereço de destino | Taxa de entrega | Registro em `order_deliveries` |
|---|---|---|---:|---|
| `DELIVERY` | Receber no endereço | Endereço ativo do cliente autenticado | Conforme regra de taxa (cálculo por distância ainda pendente) | Sim |
| `PICKUP` | Retirar no restaurante | Endereço ativo do restaurante | R$ 0,00 | Não |

Regras:

- O backend mantém `DELIVERY` como padrão quando clientes antigos não enviam `order_type`, preservando compatibilidade.
- Para `DELIVERY`, `delivery_address_id` precisa ser inteiro e pertencer ao cliente autenticado.
- Para `PICKUP`, o backend não aceita endereço de destino escolhido pelo cliente; resolve o endereço ativo do próprio restaurante. No schema atual, o ID de destino é persistido na coluna legada `orders.delivery_address_id`; a resposta distingue `delivery_address_id` e `pickup_address_id`.
- Pedidos `PICKUP` têm taxa de entrega zerada pelo servidor mesmo se o payload enviar outra taxa, e não possuem estado logístico em `order_deliveries`.
- O checkout frontend continua desabilitado. A escolha fica persistida no carrinho e ainda deverá ser enviada ao endpoint quando o fluxo de finalização for desenvolvido.
- Alterar a coluna para um nome neutro (`destination_address_id`) exige migração explícita e atualização do modelo/diagrama; não apagar o banco para contornar isso.

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

## 5. Endpoint e autorização do estado logístico

O backend expõe `PUT /pedidos/<pedido_id>/entrega/status`, protegido por `Authorization: Bearer <token>`. O corpo JSON deve conter `{"status":"PROCURANDO"}` usando um valor válido da máquina de estados.

- Até existir perfil próprio de entregador, somente uma conta `BUSINESS` vinculada ao restaurante do pedido pode alterar o estado logístico.
- Contas de cliente (`PERSONAL`) e outros restaurantes recebem `403`; pedidos inexistentes retornam `404`.
- Pedidos `PICKUP` não têm fluxo logístico e retornam `409`.
- Transições fora da máquina e conclusão antes de o pedido poder passar para `ENTREGUE` retornam `409` sem persistir a mudança.
- Ao transitar a entrega para `ENTREGA_CONCLUIDA`, a mesma transação grava `concluida_em`, `pedido.delivered_at` e o status do pedido `ENTREGUE`.

### Histórico

As transições relevantes devem ser auditáveis. A implementação completa do histórico deverá registrar, no mínimo, pedido, estado anterior, novo estado, ator/evento, data e observação quando aplicável. Essa tabela de histórico ainda não existe no modelo físico e deve ser tratada em tarefa posterior, com migração explícita.

## 6. Pagamento do pedido

Para o fluxo de pedidos do cliente, as modalidades são:

- `PIX`
- `CARTAO_CREDITO`

`MERCADO_PAGO` e `PAYPAL` representam provedores/integradores, não modalidades de pagamento.

A bandeira do cartão não será tratada como uma regra fixa do CandyLand. Quando houver integração real, o provedor deverá informar/validar a bandeira e os meios efetivamente disponíveis. O sistema deve armazenar a modalidade escolhida e, quando aplicável, os metadados retornados pelo provedor.

O pedido permanece em `PENDENTE_PAGAMENTO` até receber uma confirmação válida do provedor. Somente depois da confirmação o pedido pode avançar para `RESTAURANTE_RECEBEU`.

`BOLETO` não faz parte do checkout do pedido do cliente neste escopo. Pode ser reavaliado em uma futura funcionalidade de fornecedor/abastecimento de estoque, caso esse extra seja aprovado pelo grupo.

## 7. Regra de sincronização

Sempre que este fluxo for alterado:

1. atualizar este documento;
2. atualizar os testes de regras de negócio;
3. atualizar o modelo físico em `docs/modelo-dados.md` se houver alteração de estrutura;
4. implementar a mudança;
5. executar a suíte de testes antes do merge em `dev`.


## 8. Situação da implementação observada na auditoria (11/10/2026)

| Item | Estado no código atual | Pendência para considerar concluído |
|---|---|---|
| Estado inicial | `OrderService.criar_pedido()` grava `PENDENTE_PAGAMENTO`; o default do modelo foi alinhado ao mesmo valor. | Adicionar testes de endpoint para garantir o estado em todas as formas de criação. |
| Confirmação de pagamento | Existe `OrderService.confirmar_pagamento()` e a lógica reduz estoque. | Não há endpoint/webhook autenticado/verificado para acionar o método; integração de provedor ausente. |
| Cancelamento e reposição | Serviço de cancelamento tenta repor estoque após pagamento/andamento e cancelar a entrega. | Testar estoque real, falhas transacionais e cancelamento repetido para evitar reposição em duplicidade. |
| Máquina de estados | `order_workflow_service.py` valida transições; `PUT /pedidos/<id>/entrega/status` exige token e restringe alteração ao restaurante dono. Conclusão logística sincroniza para `ENTREGUE`. | Falta tabela de histórico auditável, papel próprio de entregador e cobertura ponta a ponta. |
| Histórico | Não há tabela própria de histórico de transições no modelo atual. | Aprovar estrutura de auditoria antes de ampliar uso operacional. |
| Taxa de entrega | O modelo guarda `taxa_entrega_base` e `raio_entrega_km`. | A taxa do pedido ainda pode vir no payload; calcular no servidor e validar a área atendida. |

A presença de métodos internos não equivale a funcionalidade acessível de ponta a ponta. O README registra os percentuais estimados e o plano para fechar essas lacunas.
