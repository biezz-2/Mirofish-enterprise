import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@locales': path.resolve(__dirname, '../locales')
    }
  },
  server: {
    port: 3001,
    open: false,
    allowedHosts: true,
    headers: {
      'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
    },
    hmr: {
      clientPort: 443
    },
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: process.env.BACKEND_URL || 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      },
      '/openapi.json': {
        target: process.env.BACKEND_URL || 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      },
      '/openapi.yaml': {
        target: process.env.BACKEND_URL || 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
