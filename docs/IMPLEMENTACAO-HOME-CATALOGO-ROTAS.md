# Home pública, catálogo, carrinho e rotas

## O que muda

- A home passa a listar produtos e docerias sem login. A pesquisa consulta `GET /produtos/busca?q=...`.
- O cliente pode abrir lojas, carregar imagens com Coil e montar carrinho local. O carrinho fica em SharedPreferences e contém apenas snapshot de produto/quantidade; preço e estoque são recalculados pelo backend.
- Login é solicitado somente ao tentar finalizar. Após autenticar, o app abre o carrinho já restaurado.
- A sessão é apagada e o app retorna à home pública quando qualquer chamada autenticada que enviou Bearer receber HTTP 401.
- A localização do celular é opcional e solicitada apenas ao tocar no botão. Distâncias da home são aproximações Haversine locais, sem consumo da Routes API.
- No checkout, o pedido é criado primeiro. O app mostra subtotal, desconto, frete e total e só inicia o gateway quando o cliente toca em “Confirmar e pagar”.
- O backend calcula a taxa com a distância rodoviária da Routes API, se habilitada; sem chave/integração, preserva a estimativa Haversine legada. A rota/tempo retornados pelo Google não são gravados no banco. A coluna legada `delivery_distance_km` continua guardando apenas a distância em linha reta.

## Proteção do consumo Google Routes

- Uma chamada `ComputeRoutes` por criação de pedido `DELIVERY`; a home e a rota de estimativa legada `/pedidos/taxa-entrega` não chamam Routes. A home não usa Route Matrix.
- `TRAFFIC_UNAWARE` e FieldMask restrito a `routes.distanceMeters,routes.duration`, para manter o uso no SKU Essentials. A tela de confirmação mostra a atribuição textual “Google Maps” junto aos dados de rota.
- Contador persistente e atômico no banco compartilhado, com limites padrão/hard cap de 100 chamadas/dia e 4.000/mês. Os valores no `.env` podem reduzir os limites, mas não elevá-los. O contador reserva a chamada antes de acessar o Google; falhas de rede também contam, por segurança.
- A reserva de cota ocorre antes da chamada. Falha de quota ou falha da API interrompe a criação de entrega; o cliente pode escolher retirada.
- Não armazenar em cache ou persistir distância/duração de rota do Google. A localização da pessoa é usada apenas em memória no Android para distâncias aproximadas locais.

## Variáveis backend

```dotenv
GOOGLE_MAPS_ROUTES_API_KEY=
GOOGLE_MAPS_ROUTES_ENABLED=true
GOOGLE_MAPS_ROUTES_MONTHLY_LIMIT=4000
GOOGLE_MAPS_ROUTES_DAILY_LIMIT=100
```

Quando `GOOGLE_MAPS_ROUTES_API_KEY` ficar vazia, o código usa `GOOGLE_MAPS_GEOCODING_API_KEY`. A chave deve ser restrita no Google Cloud às APIs Geocoding e Routes, e permanecer apenas no backend. Configure também uma quota de taxa por minuto no Console (por exemplo, 5 chamadas/min no início). O contador interno cobre apenas chamadas feitas por esta instância do CandyLand; qualquer outro sistema que reutilize a mesma chave não entra nesse contador.

## Testes

Rode a suíte de backend com `pytest`. Os testes `test_google_routes_quota.py` validam limites diário/mensal, e `test_delivery_routes_integration.py` verifica que o endpoint de estimativa não chama Routes e que somente a criação válida do pedido usa a rota real.

No Android Studio, sincronize Gradle e execute o app. O primeiro pedido de entrega calcula a rota e mostra a cobrança antes de abrir Pix/PayPal.
