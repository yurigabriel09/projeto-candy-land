# Frontend — aplicação web

Aplicação React com Vite que apresenta a jornada do cliente (catálogo, carrinho, checkout, histórico e tracking) e a área do restaurante (cadastro, configuração, pedidos, produtos e finanças).

## Arquivos da raiz

- `.dockerignore`: exclui dependências/arquivos locais do build Docker.
- `.env.example`: variáveis de ambiente esperadas no frontend; não incluir segredo privado.
- `Dockerfile`: imagem da aplicação para build/publicação.
- `index.html`: documento HTML inicial carregado pelo Vite.
- `nginx.conf`: configuração do servidor estático/reverse proxy usado na publicação.
- `package.json`: scripts e dependências diretas.
- `package-lock.json`: versões resolvidas das dependências npm.
- `vite.config.js`: configuração do Vite e proxy de desenvolvimento.

## Código-fonte (`src/`)

- `App.jsx`: rotas e composição principal. [Guia](src/README.md)
- `main.jsx`: ponto de montagem React.
- `styles.css`: estilos globais.
- `components/`: componentes compartilhados. [Guia](src/components/README.md)
- `context/`: autenticação e carrinho. [Guia](src/context/README.md)
- `hooks/`: lógica reutilizável. [Guia](src/hooks/README.md)
- `pages/`: telas. [Guia](src/pages/README.md)
- `services/`: comunicação com API. [Guia](src/services/README.md)
- `utils/`: máscaras, validação e helpers. [Guia](src/utils/README.md)
- `public/`: arquivos estáticos servidos sem processamento do Vite. [Guia](public/README.md)

## Regra de arquitetura

A tela deve cuidar de interação e apresentação; chamadas HTTP devem passar pelos services; estado compartilhado deve ficar em context/hooks. O backend é autoridade para preço final, status do pedido, pagamento, disponibilidade e estoque. Não marcar pagamento como concluído no cliente.
