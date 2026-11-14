# Registro — remoção dos controladores duplicados

**Data da análise:** 14/11/2026  
**Pasta removida pelo pacote:** `backend/app/controllers/controllers/`

## Justificativa

O backend possui o diretório oficial `backend/app/controllers/` e um subdiretório aninhado repetido `backend/app/controllers/controllers/`. A leitura das rotas ativas confirmou imports do tipo `from app.controllers.auth_controller import AuthController`, `from app.controllers.order_controller import OrderController` e equivalentes. Não há import das classes pelo caminho `app.controllers.controllers`.

## Arquivos removidos

- `auth_controller.py` — cópia/variante antiga; a versão correta permanece em `backend/app/controllers/auth_controller.py`.
- `category_controller.py` — cópia idêntica à versão oficial.
- `order_controller.py` — cópia idêntica à versão oficial.
- `payment_controller.py` — variante redundante; a versão correta permanece em `backend/app/controllers/payment_controller.py`.
- `product_controller.py` — cópia idêntica à versão oficial.
- `restaurant_controller.py` — cópia idêntica à versão oficial.
- `user_controller.py` — variante antiga; a versão correta permanece em `backend/app/controllers/user_controller.py`.

## Segurança da remoção

A exclusão é limitada ao subdiretório repetido. Os sete controladores oficiais do diretório pai são preservados. O script de aplicação valida os hashes Git esperados dos sete arquivos e pesquisa referências Python ao namespace duplicado antes de remover; se o conteúdo local divergir ou surgir referência, ele interrompe o processo.

## Verificação após aplicar

Na raiz do backend, executar:

```powershell
git grep -n -I -E 'app\.controllers\.controllers|from[[:space:]].*controllers\.controllers' -- backend
```

O comando não deve retornar ocorrências. Em seguida, executar a suíte de testes do backend e iniciar a API para validar registro de blueprints. A auditoria desta sessão não executou esses testes.
