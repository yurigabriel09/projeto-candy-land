REGRAS DE NEGÓCIO DO SISTEMA

1. PEDIDOS
- Todo pedido deve estar vinculado a um usuário cadastrado.
- O pedido possui status: Pendente, Processando, Concluído, Cancelado.
- Não é possível alterar um pedido após finalizado.

2. PAGAMENTO
- Formas de pagamento permitidas: PIX, Cartão de Crédito, Boleto.
- O pedido permanece "Pendente" até a confirmação do pagamento.
- Falhas no pagamento devem notificar o usuário e liberar a reserva dos itens.

3. ESTOQUE
- A compra só pode ser efetuada se a quantidade em estoque for maior que zero.
- O estoque é debitado assim que o pagamento é confirmado.
- Se a compra for cancelada, a quantidade de produtos deve retornar ao estoque.