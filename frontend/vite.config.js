import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Para desenvolvimento local com um único endpoint público do ngrok:
// o navegador acessa o Vite e os caminhos da API são encaminhados ao Flask.
// Configure NGROK_FRONTEND_HOST com o hostname exato do endpoint.
const ngrokFrontendHost = (process.env.NGROK_FRONTEND_HOST || '').trim()

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    allowedHosts: ngrokFrontendHost ? [ngrokFrontendHost] : [],
    proxy: {
      '^/(auth|users|restaurantes|produtos|categorias|pedidos|uploads)(/|$)': {
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
