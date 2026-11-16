# Home pública — pesquisa de endereço e distância das lojas

## Fluxo da pesquisa

1. A pessoa informa o endereço de entrega na barra da Home e seleciona **Buscar**.
2. O frontend envia o texto para `POST /restaurantes/geocodificar-endereco/publico`.
3. O backend consulta a Google Geocoding API com `GOOGLE_MAPS_GEOCODING_API_KEY`, mantida exclusivamente no servidor. O endpoint aceita endereços de 8 a 250 caracteres, restringe o resultado ao Brasil e não grava o endereço pesquisado.
4. A resposta contém `latitude`, `longitude` e `endereco_localizado`. A Home mantém essa seleção apenas na sessão do navegador (`sessionStorage`).
5. O catálogo público `GET /restaurantes` inclui `latitude` e `longitude` da localização comercial cadastrada para cada loja, quando disponíveis. Os demais dados privados da empresa continuam fora do serializer público.
6. A Home calcula a distância em linha reta pelo método Haversine e permite ordenar as lojas por distância. Lojas sem coordenadas cadastradas não exibem distância e ficam no fim da ordenação.

## Contrato do endpoint

`POST /restaurantes/geocodificar-endereco/publico`

Corpo:

```json
{
  "endereco": "Avenida Paulista, 1000, Bela Vista, São Paulo, SP"
}
```

Resposta `200`:

```json
{
  "mensagem": "Endereço localizado no mapa.",
  "dados": {
    "latitude": -23.561414,
    "longitude": -46.655881,
    "endereco_localizado": "Avenida Paulista, São Paulo - SP, Brasil"
  }
}
```

Erros esperados: `400` para texto vazio/incompleto ou maior que 250 caracteres, `422` quando o provedor não encontra o endereço, `502` para indisponibilidade/resposta inválida do provedor e `503` quando a chave de geocoding não está configurada.

## Configuração e limites

Configure `GOOGLE_MAPS_GEOCODING_API_KEY` no `backend/.env` e habilite a API Geocoding no projeto Google Cloud associado. A chave não deve ser enviada ao frontend, commitada nem incluída em ZIPs. Cada envio explícito do formulário gera uma consulta ao provedor; a Home não geocodifica a cada tecla digitada.

A localização fica em `sessionStorage` durante a sessão do navegador; o endereço e as coordenadas não são colocados na URL nem persistidos no banco de dados. A distância exibida é uma estimativa geográfica em linha reta entre as coordenadas, não o trajeto rodoviário nem uma confirmação de cobertura de entrega. A taxa final e a elegibilidade de entrega continuam sendo validadas pelo backend no checkout.

## Interface

- Cabeçalho da Home pública: fixo, responsivo, com a marca atual, link `Seja Cliente` e ações `Entrar`/`Cadastrar`.
- Cabeçalho da página de parceiros: fixo e responsivo, mantendo a identidade existente.
- Banner de entregas da Home: CTA `Seja Parceiro`, apontando para `/parceiros`; não apresenta um cadastro de entregador inexistente.
