# `backend/app/` — pacote principal

- `__init__.py`: marca `app` como pacote Python; atualmente vazio.
- `config/`: configurações e leitura de variáveis de ambiente.
- `controllers/`: camada HTTP que recebe dados já extraídos da requisição e devolve respostas Flask.
- `database/`: conexão SQLAlchemy e migrações controladas.
- `models/`: modelos ORM e relacionamentos.
- `routes/`: registro de endpoints em blueprints.
- `services/`: lógica de negócio, provedores externos e orquestração dos fluxos.
- `utils/`: autenticação transversal, datas, formatação e upload.

Mantenha dependências direcionadas: rotas chamam controladores; controladores chamam serviços; serviços usam modelos e adaptadores. Evite importar rotas dentro de serviços ou duplicar regras no frontend.
