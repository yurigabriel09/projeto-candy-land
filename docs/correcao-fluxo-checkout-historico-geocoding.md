# Correções do checkout, histórico e geocodificação — CandyLand

## Por que o Mercado Pago não voltou automaticamente?

O log fornecido mostra que o pagamento foi aprovado no sandbox e que o backend recebeu webhooks com HTTP 200. A URL do browser, porém, ficou em `sandbox.mercadopago.com.br`. Isso normalmente acontece quando a preferência foi criada sem `auto_return=approved` ou com URL de retorno local. O adaptador só configura `auto_return` quando `MERCADO_PAGO_RETURN_URL_BASE` é HTTPS. A documentação oficial proíbe `localhost` e `127.0.0.1` em `back_urls`; o retorno automático pode levar até 40 segundos após aprovação.

No seu cenário, o ngrok exibido encaminha para o backend na porta 5000. Ele não serve como página de retorno do navegador. Abra um segundo terminal e inicie outro túnel para o frontend Vite:

```powershell
ngrok http 5173
```

Copie a URL HTTPS desse segundo túnel para `MERCADO_PAGO_RETURN_URL_BASE` no `backend/.env`. Mantenha a URL HTTPS do túnel do backend em `MERCADO_PAGO_NOTIFICATION_URL`, com o caminho `/pedidos/webhooks/mercadopago`. As URLs são diferentes porque uma redireciona o navegador ao React e a outra recebe webhooks no Flask. Reinicie o backend e crie uma nova tentativa de pagamento; preferências já criadas conservam as URLs antigas. Se o túnel gratuito mudar, atualize o `.env` novamente.

O resultado da URL de retorno não é prova de pagamento. A tela consulta o pedido e o pagamento no backend, que valida o estado com o provedor; a baixa do estoque só pode acontecer nessa confirmação validada.

## Histórico de compras e pagamentos pendentes

`/minha-conta/pagamentos-pendentes` lista somente pedidos que ainda estão em `PENDENTE_PAGAMENTO`. Por isso, após aprovação correta, é esperado que essa lista mostre zero. A nova página `/minha-conta/historico-compras` lista todos os estados e fornece acesso à tela de acompanhamento.

## Código de recebimento

Após pagamento confirmado, o cliente pode obter um PIN de seis dígitos na compra. O banco armazena somente um hash derivado com `SECRET_KEY`; o PIN não é gravado em texto puro. O restaurante responsável valida o PIN no painel. Para `PICKUP`, a validação só ocorre quando o pedido está `PRONTO_PARA_ENTREGA`; para `DELIVERY`, o pedido deve primeiro atingir `ENTREGUE`. Depois de validado, o pedido passa a `FINALIZADO`. Cinco tentativas inválidas bloqueiam o PIN até o cliente gerar um novo código.

A aplicação não possui atualmente um papel próprio de entregador. Portanto, a validação de entrega está no painel do restaurante como fluxo MVP; se houver um app de entregador, o contrato de permissão precisa ser estendido para uma identidade de entrega dedicada.

## Restaurantes não apareciam na Home

A Home filtrava `loja.ativo`, mas o serializer público `Restaurante.to_catalog_dict()` não enviava `ativo`. O valor `undefined` era tratado como falso, removendo todas as docerias da lista mesmo quando `GET /restaurantes` retornava HTTP 200. O serializer agora inclui `ativo` como booleano e mantém fora do catálogo público os dados empresariais privados.

## Geocoding retornando 503: é obrigatório pagar pelo Google?

O código retornava 503 quando `GOOGLE_MAPS_GEOCODING_API_KEY` não estava configurada. Para utilizar o Google Geocoding, é necessário ativar billing no projeto Google Cloud e habilitar a API; as solicitações são cobradas conforme o volume e SKU, então configure cotas para controlar custos. Documentação oficial: https://developers.google.com/maps/documentation/geocoding/usage-and-billing?hl=pt-br.

Para a demonstração não é obrigatório contratar Google Geocoding: o checkout agora permite informar e salvar latitude/longitude manualmente no próprio endereço ou usar a localização do navegador quando o dispositivo estiver no local correto. Depois de salvar, o mapa e o cálculo de distância usam as coordenadas persistidas e a aplicação não precisa geocodificar aquele endereço novamente. A renderização do mapa usa OpenStreetMap.
