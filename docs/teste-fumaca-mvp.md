# Teste de fumaça integrado do MVP — CandyLand

**Estado:** roteiro preparado; a execução real no navegador e com o ambiente local ainda precisa ser registrada.

## Escopo automatizado

O teste `backend/tests/integration/test_mvp_smoke.py` exercita, em sequência, os contratos Flask usados pelo fluxo principal:

1. catálogo público de restaurantes;
2. catálogo público de produtos, sem revelar a quantidade interna de estoque;
3. consulta autenticada dos endereços ativos do cliente titular;
4. criação do pedido `DELIVERY` usando preços e taxa calculados no backend;
5. consulta de detalhe e listagem do pedido pelo cliente dono;
6. pedido `PICKUP` com taxa zero e sem registro logístico;
7. bloqueio de criação de pedido sem autenticação.

A suíte usa SQLite em memória, dados fictícios e um JWT de teste. Ela não comprova login real por SMS/WhatsApp, Google ou Facebook, nem a experiência visual do browser.

## Executar testes automatizados

Na raiz do repositório:

```powershell
cd backend
python.exe -m pytest tests\integration\test_mvp_smoke.py -q
python.exe -m pytest -q
cd ..\frontend
npm run build
```

Critério automatizado de aceite: todos os testes passam e o build do frontend termina com código de saída zero.

## Roteiro manual no ambiente local

1. Configure `backend/.env` local com o banco e os provedores de autenticação necessários. Não copie segredos para o repositório nem para logs.
2. Inicie o backend e o frontend pelos scripts/documentação de ambiente do projeto. Confirme que o frontend está apontando para a URL do backend em execução.
3. Entre como cliente por um método de autenticação que esteja configurado no ambiente.
4. Abra o catálogo, selecione um restaurante aberto e adicione um produto disponível ao carrinho.
5. No carrinho, selecione `DELIVERY`, escolha um endereço ativo com latitude/longitude válidas e confirme o pedido.
6. Confirme a tela de sucesso, o código e o estado `PENDENTE_PAGAMENTO`. Compare o subtotal, a taxa e o total mostrados com a consulta do pedido no backend; a taxa é calculada por Haversine em linha reta, não por rota viária.
7. Repita com `PICKUP`. A taxa deve ser zero e não deve existir estado logístico de entrega para essa modalidade.
8. Confirme que os pedidos aparecem na listagem/detalhe da conta cliente e que outro cliente não consegue consultar o pedido.
9. Verifique que nenhum pagamento foi cobrado: checkout MVP somente registra o método escolhido. Não marque o teste como pagamento aprovado.
10. Teste os caminhos negativos: endereço inativo/alheio, produto indisponível, estoque insuficiente e tentativa de criar pedido sem sessão válida.

## Evidências a registrar

- commit testado e branch;
- resultado do arquivo de teste, suíte completa e build frontend;
- método de autenticação e ambiente usados (sem incluir tokens ou segredos);
- modalidade testada e código do pedido fictício/local (mascarar qualquer dado pessoal);
- problemas encontrados, endpoint/rota e comportamento esperado versus observado.

## Limites e itens que permanecem separados

- O teste automatizado não chama provedores OAuth/SMS reais.
- O checkout não inicia captura/cobrança de PIX ou cartão.
- A confirmação de pagamento e a baixa/restauração de estoque requerem testes próprios, idempotência e um provedor de pagamento configurado.
- A execução Docker e a comunicação entre computadores/ambientes publicados precisam de validação independente.
