# Requisitos e regras globais — CandyLand

> Documento de regras de negócio acordadas/objetivo funcional. Quando o comportamento implementado divergir, a regra descrita aqui é o critério a validar com o grupo; o desvio deve permanecer explícito no README até ser corrigido e testado.

## 1. Contas, identidade e autorização

- A plataforma possui pelo menos os perfis `PERSONAL` (cliente) e `BUSINESS` (restaurante/doceria).
- O cadastro só deve ser concluído após o processo de validação de identidade/código definido para o canal escolhido. Código deve expirar, ser de uso único e ter limite de tentativas/reenvios.
- Operações privadas exigem autenticação. O backend também deve autorizar a ação pelo tipo de conta e pelo recurso: cliente só acessa os próprios dados/pedidos; restaurante só altera sua própria configuração, produtos e pedidos recebidos.
- Endpoints públicos devem ser uma lista explícita (por exemplo, consulta de restaurantes e produtos publicados, login e callbacks OAuth necessários). Listagem pública de dados pessoais, criação/desativação irrestrita de contas e mutações de restaurante não são permitidas.
- Segredos de Google, Facebook, Brevo, Twilio, JWT e outros provedores vivem em arquivos `.env` locais/secret manager; nunca no código, README ou Git.

## 2. Restaurante, categoria e produto

- Cada produto pertence a uma doceria/restaurante e a uma categoria válida desse mesmo restaurante.
- Produtos devem possuir preço não negativo, disponibilidade e saldo de estoque. Não vender item indisponível nem quantidade superior ao estoque vigente.
- O CRUD de produtos deve ser autorizado para o restaurante proprietário. Alteração de imagem deve respeitar a estratégia definida (URL validada ou upload em armazenamento); a implementação atual tem `image_url`, mas não demonstra upload de arquivo.
- A taxa base e o raio de entrega cadastrados são configuração, não comprovam cálculo por distância.

## 3. Endereço e geolocalização

- O endereço de entrega usado em pedido precisa pertencer ao cliente autenticado e estar completo/ativo.
- Consulta de CEP pode preencher dados iniciais, mas não substitui validação de endereço e coordenadas.
- Autocomplete, geocodificação, rota e distância Google Maps são funcionalidades diferentes e só podem ser marcadas como feitas quando houver implementação e teste correspondentes.

## 4. Carrinho e criação do pedido

- Um carrinho pertence a um único restaurante por vez; trocar de restaurante exige limpar/substituir os itens depois de confirmação do usuário.
- Quantidade deve ser inteiro positivo; remover ou levar a quantidade a zero remove o item.
- `localStorage` é apenas conveniência de interface, não fonte confiável para preço, taxa ou estoque.
- Na criação do pedido, o servidor deve recarregar produtos/preços do banco, validar propriedade/estoque/disponibilidade e calcular subtotal/total. Não confiar em `delivery_fee`, desconto ou total enviados livremente pelo cliente.
- Todo pedido deve pertencer a cliente autenticado e restaurante válido. Para `DELIVERY`, o endereço de destino precisa pertencer ao cliente e estar ativo; para `PICKUP`, o destino é o endereço ativo cadastrado pelo restaurante.
- `order_type` aceita `DELIVERY` (entrega no endereço) ou `PICKUP` (retirada no restaurante). O tipo é persistido no pedido; seleção no carrinho não significa que o checkout esteja concluído.
- Pedido `PICKUP` não cobra taxa de entrega e não cria fluxo logístico em `order_deliveries`. O endereço do restaurante é guardado temporariamente na coluna legada `orders.delivery_address_id` para não quebrar o schema atual. Uma renomeação para `destination_address_id` requer migração formal futura.

## 5. Pagamento

- Modalidades de pagamento do pedido do cliente definidas até o momento: `PIX` e `CARTAO_CREDITO`.
- `MERCADO_PAGO` e `PAYPAL` são opções de **provedor**, não modalidade escolhida pelo cliente. O grupo precisa decidir qual gateway será implementado primeiro.
- O estado inicial do pedido é `PENDENTE_PAGAMENTO`. Não considerar pagamento confirmado apenas porque o frontend enviou uma requisição; a confirmação deve vir de uma integração confiável/assinada ou de fluxo de sandbox claramente separado.
- A confirmação deve ser idempotente: callbacks repetidos não podem baixar estoque nem avançar o pedido duas vezes.
- Não armazenar número completo nem CVV de cartão. Quando aplicável, guardar apenas token opaco e metadados mínimos de retorno do provedor.
- `BOLETO` fica fora do checkout do pedido do cliente. Pode ser analisado futuramente para abastecimento de estoque/fornecedor, caso seja aprovado como escopo extra.

## 6. Estoque e cancelamento

- A quantidade deve ser verificada novamente no servidor antes de confirmar a compra; validar apenas quando adiciona ao carrinho não é suficiente.
- O débito do estoque ocorre uma vez, após confirmação real do pagamento.
- Cancelamento anterior à confirmação não repõe algo que nunca foi debitado. Cancelamento posterior deve repor uma única vez conforme política de negócio e situação de produção/entrega.
- Estoque e alteração de estado precisam ser transacionais. Cenários de concorrência, retry e cancelamento repetido devem ter testes.

## 7. Pedido e entrega

- O estado comercial/operacional do pedido e o estado logístico da entrega são independentes. Detalhes, estados permitidos e cancelamentos estão em `docs/regras-pedidos.md`.
- Não permitir alteração depois de `FINALIZADO` ou `CANCELADO`; não aceitar transições fora da máquina de estados.
- A procura de motorista pode ocorrer durante a produção. Se motorista desistir durante a atribuição, a entrega pode voltar para `PROCURANDO` sem cancelar automaticamente o pedido.
- Mudanças relevantes de estado devem guardar ator/evento, estado anterior/novo e horário. A estrutura de histórico ainda precisa ser decidida/implementada.
- `order_type=DELIVERY` e `order_type=PICKUP` são os valores suportados para criação de pedido. A retirada usa o endereço ativo do restaurante, não cria `order_deliveries` e não pode receber atualização logística. O fluxo de checkout frontend ainda está desabilitado e não envia pedidos.

## 8. Comunicações e documentos fiscais

- Mensagens de autenticação por e-mail/WhatsApp e notificações de pedido/entrega são fluxos distintos. Ter cliente Brevo/Twilio no código não significa que eventos de pedido já notifiquem clientes.
- Notificações de pedido devem ocorrer após persistência do evento e tolerar retries sem duplicação indevida.
- Emissão de NFe/SEFAZ, PDF fiscal e relatórios dependem de requisitos, integração autorizada e homologação. Não declarar emitida uma nota a partir de um simples PDF.

## 9. Segurança, privacidade e observabilidade

- Não expor documentos pessoais, códigos de autenticação, tokens nem configurações secretas em respostas/logs.
- Validar entrada e limitar erros, tentativas, payloads e permissões no backend.
- Rotas públicas de leitura devem retornar apenas os campos necessários para o catálogo.
- Operações de escrita devem possuir testes de autenticação, autorização, validação e tentativa de acesso cruzado entre contas.

## 10. Regras de documentação e versionamento

- Regras globais ficam aqui; regras específicas de pedido/entrega ficam em `docs/regras-pedidos.md`.
- Mudou tabela, coluna, default, chave ou relacionamento? Atualizar `docs/modelo-dados.md`, a fonte `docs/modelo-dados.dot` e a imagem `docs/modelo-dados.png` na mesma branch.
- O README deve sempre listar tecnologias, ferramentas/integrações presentes, progresso estimado e tarefas atribuídas. Distinguir código encontrado de integração externa validada.
- O fluxo Git é: branch sempre criada a partir de `dev`; merge de feature em `dev`; merge de `dev` em `main` somente no fechamento da sprint.
- Não apagar banco para forçar compatibilidade com modelo. Fazer backup e usar migração explícita para alterações físicas. A aplicação usa `db.create_all()`, que não migra colunas existentes.
