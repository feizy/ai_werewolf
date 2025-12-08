import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/src',
    }
  },
  server: {
    port: 3000,
    proxy: {
      // REST API 代理
      '/rooms': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/games': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      // WebSocket 代理
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true,
        changeOrigin: true,
      }
    }
  }
})

