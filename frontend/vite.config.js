import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// O ngrok serve somente como ponte HTTPS exigida pelo Checkout Pro.
// Ao receber uma navegacao HTML pelo tunel, devolvemos o navegador
// ao localhost, onde o login e as chamadas da API ja funcionam.
function retornoParaLocalhost() {
  return {
    name: 'candyland-retorno-localhost',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const host = (req.headers.host || '').split(':')[0].toLowerCase();
        const tunel = host.endsWith('.ngrok-free.dev') || host.endsWith('.ngrok.io') || host.endsWith('.ngrok-free.app');
        const navegacao = req.method === 'GET' && (req.headers.accept || '').includes('text/html');

        if (!tunel || !navegacao) return next();

        // Sem redirecionamento aberto: o destino eh fixo e local.
        const url = new URL(req.url || '/', 'http://localhost:5173');
        res.statusCode = 302;
        res.setHeader('Location', `http://localhost:5173${url.pathname}${url.search}`);
        res.setHeader('Cache-Control', 'no-store');
        res.end();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), retornoParaLocalhost()],
  server: {
    host: '0.0.0.0',
    // Permite qualquer subdominio do ngrok sem precisar configurar variável de ambiente
    allowedHosts: ['.ngrok-free.dev', '.ngrok.io'],
    proxy: {
      '^/(auth|users|restaurantes|produtos|categorias|pedidos|uploads|relatorios)(/|$)': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: true,
      },
    },
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin-allow-popups',
    },
  },
})