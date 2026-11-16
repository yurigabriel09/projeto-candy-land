# `scripts/` — automações de desenvolvimento

- `gerar_zip_limpo.cmd` / `gerar_zip_limpo.ps1`: gera um pacote de código sem `.git`, ambientes virtuais, dependências baixadas, caches Gradle, uploads locais ou arquivos específicos da máquina. Não apaga dados do projeto.
- `gerenciar_pr.cmd` / `gerenciar_pr.ps1`: operações auxiliares de Pull Request.
- `preparar_ambiente.cmd` / `preparar_ambiente.ps1`: cria/reutiliza `.venv`, instala as dependências e prepara o frontend. Preserva arquivos `.env` existentes.
- `validar_projeto.cmd` / `validar_projeto.ps1`: reinstala/atualiza as dependências do backend e frontend e executa pytest e build Vite usando o Python do `.venv`.

Execute scripts a partir de qualquer diretório; eles localizam a raiz pela própria localização. Leia os parâmetros e confira a branch antes de publicar alterações.
