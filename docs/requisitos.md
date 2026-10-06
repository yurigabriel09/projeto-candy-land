REGRAS DE NEGÓCIO DO SISTEMA

1. PEDIDOS
- Todo pedido deve estar vinculado a um usuário cadastrado.
- O pedido possui um estado principal: PENDENTE_PAGAMENTO, PAGAMENTO_CONFIRMADO, RESTAURANTE_RECEBEU, RESTAURANTE_ACEITOU, PROCESSANDO, PRONTO_PARA_ENTREGA, ENTREGUE, FINALIZADO ou CANCELADO.
- O estado logístico da entrega é independente do estado principal, permitindo procurar/encontrar motorista enquanto o pedido está em PROCESSANDO.
- Não é possível alterar um pedido após FINALIZADO ou CANCELADO.
- As transições válidas estão documentadas em docs/regras-pedidos.md e devem ser validadas pelo backend.

2. PAGAMENTO
- Formas de pagamento permitidas no fluxo de pedidos: PIX e Cartão de Crédito.
- Os provedores de pagamento planejados são Mercado Pago e PayPal, conforme disponibilidade da modalidade na integração.
- O provedor é a ferramenta de processamento; não deve ser confundido com a modalidade escolhida pelo cliente.
- Para cartão, a bandeira não será fixada no modelo de negócio; ela será informada/validada conforme as bandeiras efetivamente suportadas pelo provedor configurado.
- O pedido permanece PENDENTE_PAGAMENTO até a confirmação do pagamento.
- Falhas no pagamento devem notificar o usuário e liberar a reserva dos itens.

3. ESTOQUE
- A compra só pode ser efetuada se a quantidade em estoque for maior que zero.
- O estoque é debitado assim que o pagamento é confirmado.
- Se a compra for cancelada, a quantidade de produtos deve retornar ao estoque conforme a regra de cancelamento aplicável.

4. ENTREGA
- A entrega possui ciclo próprio: NAO_SOLICITADO, PROCURANDO, MOTORISTA_ENCONTRADO, MOTORISTA_A_CAMINHO, MOTORISTA_NO_RESTAURANTE, PEDIDO_RETIRADO, EM_ROTA e ENTREGA_CONCLUIDA.
- Se um motorista cancelar durante a atribuição, o sistema pode retornar a entrega para PROCURANDO em vez de cancelar o pedido.
- A busca de motorista pode ocorrer em paralelo com a produção do pedido.

5. HISTÓRICO
- Mudanças relevantes de estado devem ser auditáveis.
- A estrutura definitiva do histórico será refletida no modelo físico documentado em docs/modelo-dados.md.


## 6. FORNECEDOR (EXTRA FUTURO)
- Uma eventual funcionalidade de compras para abastecimento de estoque é tratada como escopo extra, separado do fluxo de pedidos do cliente.
- Se implementada, será acessível somente a contas BUSINESS autorizadas e não aparecerá para clientes PERSONAL.
- Boleto pode ser avaliado nesse fluxo futuro de fornecedor, sem fazer parte do pagamento do pedido do cliente.
