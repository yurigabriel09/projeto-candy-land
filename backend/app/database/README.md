# `backend/app/database/`

- `database.py`: configura a extensão/conexão SQLAlchemy compartilhada pelos modelos e pela aplicação.
- `migrations.py`: contém migrações/ajustes de schema executados pelo backend, incluindo a adaptação de taxa de entrega por distância.

Alterações de modelo devem vir acompanhadas de migração idempotente, compatibilidade com bancos existentes e testes de upgrade. Não assumir que recriar o banco é solução para problema de fluxo.
