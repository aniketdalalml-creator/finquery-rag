import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Legacy routes live at backend root (/health, /query): strip /api.
        // Versioned routes already carry /api/v1 on the backend: pass them through.
        rewrite: (path) =>
          path.startsWith('/api/v1') ? path : path.replace(/^\/api/, ''),
      },
    },
  },
})
