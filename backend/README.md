# Backend — API e regras de negócio

API construída em Flask. O código está organizado para separar HTTP (routes/controllers), regras de negócio e integrações (services), persistência (models/database) e validações transversais (utils).

## Arquivos na raiz

- `.dockerignore`: exclui arquivos locais do contexto de build Docker.
- `.env.example`: catálogo de variáveis de configuração; preencher valores reais apenas em `.env` local, nunca versionar segredo.
- `Dockerfile`: define a imagem da API e seus passos de instalação/execução.
- `requirements.txt`: dependências Python do backend.
- `run.py`: ponto de entrada da aplicação Flask, configura extensões, registra blueprints e executa tarefas de inicialização/migração.

## Pastas

- `app/`: pacote principal da aplicação. Ver [app/README.md](app/README.md).
- `app/config/`: leitura e validação de configurações. Ver [config/README.md](app/config/README.md).
- `app/controllers/`: controladores HTTP oficiais. Ver [controllers/README.md](app/controllers/README.md).
- `app/database/`: ORM e migrações. Ver [database/README.md](app/database/README.md).
- `app/models/`: entidades e relacionamentos. Ver [models/README.md](app/models/README.md).
- `app/routes/`: rotas/blueprints e proteção de endpoints. Ver [routes/README.md](app/routes/README.md).
- `app/services/`: regras de domínio e integrações. Ver [services/README.md](app/services/README.md).
- `app/utils/`: utilitários compartilhados. Ver [utils/README.md](app/utils/README.md).
- `tests/`: testes organizados por assunto. Ver [tests/README.md](tests/README.md).

## Caminho de uma requisição

`route -> controller -> service -> model/database -> resposta`. Regras de domínio não devem ser duplicadas nos controladores nem decididas pelo frontend. Integrações externas devem ficar isoladas em serviços/adaptadores e ser cobertas por testes com mock.

## Domínios principais

Autenticação e OAuth, usuários/restaurantes, catálogo e categorias, pedidos/retirada/entrega, pagamento (PayPal/Mercado Pago/mock), taxa de entrega, código de recebimento, token de dispositivo e push.

## Execução e testes

Use `backend/.env.example` como referência, configure um ambiente Python isolado e instale `requirements.txt`. Para detalhes de comandos, confirme também as instruções atuais do README do projeto. Não há declaração nesta documentação de que os testes tenham sido executados nesta auditoria.
