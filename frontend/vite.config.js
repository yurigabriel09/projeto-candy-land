import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    // Permite qualquer subdomínio do ngrok sem precisar configurar variável de ambiente
    allowedHosts: ['.ngrok-free.dev', '.ngrok.io'],
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