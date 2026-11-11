# Ajustes de confirmação de pedido e geocodificação — 31/10/2026

## Confirmação do pedido

- A caixa de validação do PIN de seis dígitos agora aparece no painel da doceria para pedidos de entrega e retirada em `PRONTO_PARA_ENTREGA`.
- O backend aceita PIN em `PRONTO_PARA_ENTREGA` ou `ENTREGUE`.
- Quando o pedido ainda está pronto, a confirmação válida realiza a transição `PRONTO_PARA_ENTREGA` → `ENTREGUE` → `FINALIZADO` na mesma transação. Não depende de uma ação adicional que não existia na interface.
- O PIN continua armazenado somente como hash e mantém o limite de cinco tentativas inválidas.

## Geocodificação dinâmica

- Foi criada uma chamada backend para a API Google Geocoding, protegendo a chave de API.
- No cadastro empresarial, a consulta exige uma tentativa de cadastro com e-mail e telefone verificados.
- Na configuração, a consulta exige autenticação e titularidade do restaurante.
- A interface aguarda um curto intervalo após a edição do endereço, descarta respostas antigas e atualiza latitude/longitude automaticamente.
- Quando o geocoding funciona, exibe o mapa e oculta os campos numéricos. Quando falha ou não está configurado, apresenta os campos manuais e a opção de localização do navegador.
- O mapa continua usando OpenStreetMap para renderização e atribuição já existentes no componente.

## Configuração necessária

Configure `GOOGLE_MAPS_GEOCODING_API_KEY` no arquivo local `backend/.env`, com a API Geocoding habilitada no Google Cloud. A chave não deve ser adicionada ao Git. Sem ela, o fluxo manual é exibido automaticamente.

## Verificações executadas nesta geração

- `py_compile` passou nos arquivos Python modificados.
- A execução de pytest no ambiente de criação deste ZIP não foi possível porque o container não possui Flask instalado. Os testes foram adicionados/atualizados, mas precisam ser executados no `.venv` local do projeto.
- O build completo do Vite também não foi executado neste ambiente; verifique com `npm ci` e `npm run build` na máquina do projeto.
