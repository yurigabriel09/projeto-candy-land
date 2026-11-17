# Portal do Vendedor — Android

O aplicativo identifica o tipo de conta retornado pelo fluxo de autenticação (`PERSONAL` ou `BUSINESS`). Uma conta `BUSINESS` abre `BusinessSellerScreen`, em vez da área de compras.

## Recursos

- Painel com nome e status operacional da doceria, resumo de produtos e pedidos.
- Aba Cardápio para criar/editar produtos e criar as categorias padrão da plataforma; nome, descrição, preço, estoque, disponibilidade, indicador de importado e personalização são preservados.
- Abertura/fechamento da doceria apenas quando a conta já está liberada (`ABERTO`/`FECHADO`). `EM_ANALISE` informa ao vendedor que a aprovação ainda está pendente.
- Consulta de pedidos confirmados pelo gateway e atualização das etapas de preparo.
- Fluxo de entrega até `ENTREGA_CONCLUIDA` e validação do código de recebimento fornecido pelo cliente.
- Configuração sincronizada ao endpoint web `/restaurantes/{id}/configuracao`, incluindo nome, descrição, valores, horário e endereço comercial.
- Cadastro/edição do endereço comercial somente com campos textuais. O backend resolve latitude e longitude usando o Geocoding API; o vendedor não precisa conhecer coordenadas.
- Registro do token FCM para receber atualizações de pedidos no aparelho.

## Limites atuais

O app oferece cadastro/edição de produtos e categorias, mas o envio de fotos de produtos continua disponível pelo portal web. O backend não oferece fluxo de tokenização de cartões salvos; portanto, o app não coleta número completo ou CVV. O checkout continua encaminhando o pagamento ao provedor configurado.

## Segurança de status

Uma doceria em `EM_ANALISE` aparece na vitrine pública com o rótulo de aprovação pendente, mas não pode receber pedidos. O app desabilita o botão de abertura antes da aprovação e o backend rejeita pedidos até o restaurante estar `ABERTO`.
