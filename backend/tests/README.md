# `backend/tests/` — testes automatizados

A suíte é dividida por domínio:

- `authentication/`: códigos, identidade, login e OAuth.
- `business_rules/`: pedidos, pagamento, estoque, entrega, catálogo, geocoding, restaurantes e adaptadores.
- `checkout/`: endpoints e contrato de checkout.
- `integration/`: fluxos ponta a ponta/smoke do MVP.
- `notifications/`: registro e propriedade de tokens de dispositivo.
- `security/`: autorização e proteção da API.

## Executar no Windows

Na raiz do repositório, instale as dependências no ambiente virtual do próprio projeto e execute a suíte usando o mesmo interpretador:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
Set-Location .\backend
..\.venv\Scripts\python.exe -m pytest -q
Set-Location ..
```

Não use um `python` global diferente do `.venv`. O módulo `reportlab` é obrigatório porque o controller de pedidos importa o serviço de comprovantes PDF durante a inicialização; sem a instalação de `backend/requirements.txt`, a coleta dos testes de pedidos falha antes de executar qualquer teste.

A validação completa (instalação Python + `npm ci` + pytest + build Vite) pode ser executada da raiz com `scripts/validar_projeto.cmd`. Registre no PR o resultado real de cada etapa; não marque a suíte como aprovada se a coleta ou o build forem interrompidos.
